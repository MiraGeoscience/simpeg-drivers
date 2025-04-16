# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
import simpeg.electromagnetics.frequency_domain.sources as fem_sources
import simpeg.electromagnetics.natural_source.sources as ns_sources
import simpeg.electromagnetics.static.resistivity.sources as dc_sources
import simpeg.electromagnetics.time_domain.sources as tem_sources
import simpeg.potential_fields.gravity.sources as grav_sources
import simpeg.potential_fields.magnetics.sources as mag_sources
from geoh5py.objects import LargeLoopGroundTEMReceivers

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.options import BaseOptions


class SourcesFactory(SimPEGFactory):
    """Build SimPEG sources objects based on factory type."""

    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Options object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        if self.factory_type in ["magnetic vector", "magnetic scalar"]:
            return mag_sources.UniformBackgroundField

        elif self.factory_type == "gravity":
            return grav_sources.SourceField

        elif "direct current" in self.factory_type:
            return dc_sources.Dipole

        elif "induced polarization" in self.factory_type:
            return dc_sources.Dipole

        elif "fdem" in self.factory_type:
            if "fdem 1d" == self.factory_type and np.allclose(
                np.kron(
                    np.ones((len(self.params.data_object.channels), 1)),
                    self.params.data_object.vertices,
                ),
                self.params.data_object.complement.vertices,
            ):
                return fem_sources.CircularLoop

            return fem_sources.MagDipole

        elif "tdem" in self.factory_type:
            if isinstance(self.params.data_object, LargeLoopGroundTEMReceivers):
                return tem_sources.LineCurrent

            if "tdem 1d" == self.factory_type and np.allclose(
                self.params.data_object.vertices,
                self.params.data_object.complement.vertices,
            ):
                return tem_sources.CircularLoop

            return tem_sources.MagDipole

        elif self.factory_type in ["magnetotellurics", "tipper"]:
            return ns_sources.PlanewaveXYPrimary

    def assemble_arguments(
        self,
        receivers=None,
        locations=None,
        frequency=None,
        waveform=None,
    ):  # pylint: disable=arguments-differ
        """Provides implementations to assemble arguments for sources object."""
        _ = waveform
        args = []

        if self.factory_type in [
            "direct current pseudo 3d",
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
            "induced polarization pseudo 3d",
        ]:
            args += self._dcip_arguments(
                receivers=receivers,
                locations=locations,
            )

        elif self.factory_type in ["fdem", "fdem 1d", "magnetotellurics", "tipper"]:
            args.append(receivers)
            args.append(frequency)

        elif "tdem" in self.factory_type:
            args.append(receivers)

        else:
            args.append([receivers])

        return args

    def assemble_keyword_arguments(  # pylint: disable=arguments-differ
        self, receivers=None, locations=None, frequency=None, waveform=None
    ):
        """Provides implementations to assemble keyword arguments for receivers object."""
        _ = (receivers, frequency)
        kwargs = {}
        if self.factory_type in ["magnetic scalar", "magnetic vector"]:
            kwargs = {
                "amplitude": self.params.inducing_field_strength,
                "inclination": self.params.inducing_field_inclination,
                "declination": self.params.inducing_field_declination,
            }
        if self.factory_type in ["magnetotellurics", "tipper"]:
            background = deepcopy(self.params.background_conductivity)

            if getattr(self.params, "model_type", None) == "Resistivity (Ohm-m)":
                background **= -1.0

            kwargs["sigma_primary"] = [background]

        if "fdem" in self.factory_type:
            kwargs["location"] = locations
        if "tdem" in self.factory_type:
            kwargs["location"] = locations
            kwargs["waveform"] = waveform

        if "1d" in self.factory_type:
            if isinstance(
                self.concrete_object(),
                tem_sources.CircularLoop | fem_sources.CircularLoop,
            ):
                kwargs["moment"] = 1.0
            else:
                kwargs["current"] = 1.0
                kwargs["radius"] = np.pi**-0.5

        return kwargs

    def build(  # pylint: disable=arguments-differ
        self, receivers=None, locations=None, frequency=None, waveform=None
    ):
        return super().build(
            receivers=receivers,
            locations=locations,
            frequency=frequency,
            waveform=waveform,
        )

    def _dcip_arguments(self, receivers=None, locations=None):
        args = []

        locations_a = locations[0]
        locations_b = locations[1]
        args.append([receivers])
        args.append(locations_a)

        if np.all(locations_a == locations_b):
            self.simpeg_object = dc_sources.Pole
        else:
            args.append(locations_b)

        return args
