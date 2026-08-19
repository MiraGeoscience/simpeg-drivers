# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=W0613
# pylint: disable=W0221

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.options import BaseOptions

import numpy as np
from geoapps_utils.utils.transformations import x_rotation_matrix, z_rotation_matrix
from geoh5py.objects.surveys.electromagnetics.base import (
    AirborneEMSurvey,
    LargeLoopGroundEMSurvey,
)

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.utils.regularization import direction_and_dip, get_cell_normals


ORIENTATION_MAP = {
    "coplanar": "z",
    "coaxial": "y",
    "vertical": "z",
    "inline": "y",
    "crossline": "x",
}


class ReceiversFactory(SimPEGFactory):
    """Build SimPEG receivers objects based on factory type."""

    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Options object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()
        self.orientations = self.validate_orientations()

    def concrete_object(self):
        if self.factory_type in [
            "magnetic vector",
            "magnetic scalar",
            "magnetic vector pde",
        ]:
            from simpeg.potential_fields.magnetics import receivers

            return receivers.Point

        elif self.factory_type == "gravity":
            from simpeg.potential_fields.gravity import receivers

            return receivers.Point

        elif "direct current" in self.factory_type:
            from simpeg.electromagnetics.static.resistivity import receivers

            return receivers.Dipole

        elif "induced polarization" in self.factory_type:
            from simpeg.electromagnetics.static.induced_polarization import receivers

            return receivers.Dipole

        elif "fdem" in self.factory_type:
            from simpeg.electromagnetics.frequency_domain import receivers

            if "1d" in self.factory_type:
                return receivers.PointMagneticFieldSecondary

            return receivers.PointMagneticFluxDensitySecondary

        elif "tdem" in self.factory_type:
            from simpeg.electromagnetics.time_domain import receivers

            if "dB/dt" in self.params.data_units:
                return receivers.PointMagneticFluxTimeDerivative
            elif "B (T" in self.params.data_units:
                return receivers.PointMagneticFluxDensity
            else:
                return receivers.PointMagneticField

        elif self.factory_type == "magnetotellurics":
            from simpeg.electromagnetics.natural_source import receivers

            return receivers.Impedance

        elif self.factory_type == "tipper":
            from simpeg.electromagnetics.natural_source import receivers

            return receivers.Tipper

        elif self.factory_type == "apparent conductivity":
            from simpeg.electromagnetics.natural_source import receivers

            return receivers.ApparentConductivity

    def assemble_arguments(
        self,
        locations=None,
        data=None,
        local_indices=None,
        component=None,
    ):
        """Provides implementations to assemble arguments for receivers object."""

        args = []

        if (
            "direct current" in self.factory_type
            or "induced polarization" in self.factory_type
        ):
            args += self._dcip_arguments(
                locations=locations,
                local_indices=local_indices,
            )
        elif self.factory_type in [
            "apparent conductivity",
            "magnetotellurics",
            "tipper",
        ]:
            args += self._base_station_arguments(
                locations=locations,
            )
        elif "tdem" in self.factory_type:
            args += self._tdem_arguments(
                data=data,
                locations=locations,
            )

        else:
            args.append(locations)

        return args

    def assemble_keyword_arguments(
        self,
        locations=None,
        data=None,
        local_indices=None,
        component=None,
    ):
        """Provides implementations to assemble keyword arguments for receivers object."""
        kwargs = {}
        if self.factory_type in [
            "gravity",
            "magnetic scalar",
            "magnetic vector",
            "magnetic vector pde",
        ]:
            kwargs["components"] = list(data)
        else:
            kwargs["storeProjections"] = True

        # Channels such as txz_real or zxy_imag
        if self.factory_type in ["magnetotellurics", "tipper"]:
            ori, comp = component.split("_")
            kwargs["orientation"] = ori[1:]
            kwargs["component"] = comp

        # Channels such as real
        if self.factory_type in ["fdem", "fdem 1d"]:
            comp, ori = component.split("_")
            kwargs["orientation"] = ORIENTATION_MAP[ori]
            kwargs["component"] = comp

        if self.factory_type in ["tipper"]:
            kwargs["orientation"] = kwargs["orientation"][::-1]

        if "tdem" in self.factory_type:
            kwargs["orientation"] = ORIENTATION_MAP[component]

        if self.factory_type == "fdem 1d":
            kwargs["data_type"] = "ppm"

        # Overload orientation if provided
        if (
            isinstance(
                self.params.data_object, AirborneEMSurvey | LargeLoopGroundEMSurvey
            )
            and local_indices is not None
        ):
            orientations = self.orientations[kwargs["orientation"]][local_indices, :]
            kwargs["orientation"] = orientations

        return kwargs

    def _dcip_arguments(self, locations=None, local_indices=None):
        args = []
        local_indices = np.vstack(local_indices)

        args.append(locations[local_indices[:, 0], :])

        if np.all(local_indices[:, 0] == local_indices[:, 1]):
            if "direct current" in self.factory_type:
                from simpeg.electromagnetics.static.resistivity import receivers
            else:
                from simpeg.electromagnetics.static.induced_polarization import (
                    receivers,
                )
            self.simpeg_object = receivers.Pole
        else:
            args.append(locations[local_indices[:, 1], :])

        return args

    def _tdem_arguments(self, data=None, locations=None):
        return [
            locations,
            np.asarray(data.entity.channels) * self.params.unit_conversion,
        ]

    def _base_station_arguments(self, locations=None):
        if getattr(self.params.data_object, "base_stations", None) is None:
            return [locations]

        stations = self.params.data_object.base_stations.vertices
        if (
            stations is not None
            and stations.shape[0] != self.params.data_object.n_vertices
        ):
            station_ids = (
                self.params.data_object.tx_id_property.values - 1
            )  # Reference ids start at 1
            stations = stations[station_ids, :]

        # E-field on base stations and H-field locations
        if self.factory_type == "apparent conductivity":
            return stations, locations

        # H-field on locations with base stations
        return locations, stations

    def validate_orientations(self):
        """
        Validate the various options for the orientation parameter and
        return an orientation array of shape (n_receivers, 3) for use in SimPEG receivers.
        """
        n_recs = self.params.data_object.n_vertices
        normals = {
            comp: get_cell_normals(n_recs, comp, True, 3).reshape((-1, 3))
            for comp in "xyz"
        }

        if getattr(self.params, "receivers_orientation", None):
            azm, dip = direction_and_dip(self.params.receivers_orientation)
            azi_dip = np.deg2rad(np.c_[azm.values, dip.values])
            orientations = {}
            for axis in "xyz":
                orientations[axis] = (
                    z_rotation_matrix(-azi_dip[:, 0])
                    * (x_rotation_matrix(-azi_dip[:, 1]) * normals[axis].flatten())
                ).reshape((-1, 3))

            return orientations

        # elif "borehole" in self.params.inversion_type:
        #     pass

        return normals
