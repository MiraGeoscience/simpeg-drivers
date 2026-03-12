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
        local_index=None,
        component=None,
        orientation=None,
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
        local_index=None,
        component=None,
        orientation=None,
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

        # Overload orientation if provided
        if self.factory_type in ["tdem", "fdem"] and orientation is not None:
            kwargs["orientation"] = orientation

        return kwargs

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
