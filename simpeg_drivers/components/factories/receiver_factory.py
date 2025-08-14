# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
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
from geoapps_utils.utils.transformations import rotate_xyz

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


class ReceiversFactory(SimPEGFactory):
    """Build SimPEG receivers objects based on factory type."""

    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Options object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        if self.factory_type in ["magnetic vector", "magnetic scalar"]:
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

            if self.params.data_units == "dB/dt (T/s)":
                return receivers.PointMagneticFluxTimeDerivative
            elif self.params.data_units == "B (T)":
                return receivers.PointMagneticFluxDensity
            else:
                return receivers.PointMagneticField

        elif self.factory_type == "magnetotellurics":
            from simpeg.electromagnetics.natural_source import receivers

            return receivers.Impedance

        elif self.factory_type == "tipper":
            from simpeg.electromagnetics.natural_source import receivers

            return receivers.Tipper

    def assemble_arguments(
        self, locations=None, data=None, local_index=None, component=None
    ):
        """Provides implementations to assemble arguments for receivers object."""

        args = []

        if (
            "direct current" in self.factory_type
            or "induced polarization" in self.factory_type
        ):
            args += self._dcip_arguments(
                locations=locations,
                local_index=local_index,
            )

        elif self.factory_type in ["magnetotellurics"]:
            args += self._magnetotellurics_arguments(
                locations=locations,
                local_index=local_index,
            )

        elif "tdem" in self.factory_type:
            args += self._tdem_arguments(
                data=data,
                locations=locations,
                local_index=local_index,
            )

        else:
            args.append(locations[local_index])

        return args

    def assemble_keyword_arguments(
        self, locations=None, data=None, local_index=None, component=None
    ):
        """Provides implementations to assemble keyword arguments for receivers object."""
        kwargs = {}
        if self.factory_type in ["gravity", "magnetic scalar", "magnetic vector"]:
            kwargs["components"] = list(data)
        else:
            kwargs["storeProjections"] = True

        if self.factory_type in ["fdem", "fdem 1d", "magnetotellurics", "tipper"]:
            comp = component.split("_")[0]
            kwargs["orientation"] = comp[0] if "fdem" in self.factory_type else comp[1:]
            kwargs["component"] = component.split("_")[1]
        if self.factory_type in ["tipper"]:
            kwargs["orientation"] = kwargs["orientation"][::-1]
        if "tdem" in self.factory_type:
            kwargs["orientation"] = component

        if self.factory_type == "fdem 1d":
            kwargs["data_type"] = "ppm"

        return kwargs

    def build(self, locations=None, data=None, local_index=None, component=None):
        receivers = super().build(
            locations=locations,
            data=data,
            local_index=local_index,
            component=component,
        )

        if (
            self.factory_type in ["tipper"]
            and getattr(self.params.data_object, "base_stations", None) is not None
        ):
            stations = self.params.data_object.base_stations.vertices
            if stations is not None:
                if stations.shape[0] == 1:
                    stations = np.tile(stations.T, self.params.data_object.n_vertices).T

                receivers.reference_locations = stations[local_index, :]

        return receivers

    def _dcip_arguments(self, locations=None, local_index=None):
        args = []
        local_index = np.vstack(local_index)

        args.append(locations[local_index[:, 0], :])

        if np.all(local_index[:, 0] == local_index[:, 1]):
            if "direct current" in self.factory_type:
                from simpeg.electromagnetics.static.resistivity import receivers
            else:
                from simpeg.electromagnetics.static.induced_polarization import (
                    receivers,
                )
            self.simpeg_object = receivers.Pole
        else:
            args.append(locations[local_index[:, 1], :])

        return args

    def _tdem_arguments(self, data=None, locations=None, local_index=None):
        return [
            locations,
            np.asarray(data.entity.channels) * self.params.unit_conversion,
        ]

    def _magnetotellurics_arguments(self, locations=None, local_index=None):
        args = []
        locs = locations[local_index]

        args.append(locs)

        return args
