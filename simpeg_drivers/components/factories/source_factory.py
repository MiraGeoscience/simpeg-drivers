# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

from copy import deepcopy

import numpy as np
from geoapps_utils.utils.transformations import rotate_xyz
from geoh5py.objects import LargeLoopGroundTEMReceivers

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


class SourcesFactory(SimPEGFactory):
    """Build SimPEG sources objects based on factory type."""

    def __init__(self, params: BaseParams):
        """
        :param params: Params object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        if self.factory_type in ["magnetic vector", "magnetic scalar"]:
            from simpeg.potential_fields.magnetics import sources

            return sources.UniformBackgroundField

        elif self.factory_type == "gravity":
            from simpeg.potential_fields.gravity import sources

            return sources.SourceField

        elif "direct current" in self.factory_type:
            from simpeg.electromagnetics.static.resistivity import sources

            return sources.Dipole

        elif "induced polarization" in self.factory_type:
            from simpeg.electromagnetics.static.induced_polarization import sources

            return sources.Dipole

        elif "fem" in self.factory_type:
            from simpeg.electromagnetics.frequency_domain import sources

            return sources.MagDipole

        elif "tdem" in self.factory_type:
            from simpeg.electromagnetics.time_domain import sources

            if isinstance(self.params.data_object, LargeLoopGroundTEMReceivers):
                return sources.LineCurrent
            else:
                return sources.MagDipole

        elif self.factory_type in ["magnetotellurics", "tipper"]:
            from simpeg.electromagnetics.natural_source import sources

            return sources.PlanewaveXYPrimary

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

        if locations is not None and getattr(self.params.mesh, "rotation", None):
            locations = rotate_xyz(
                locations,
                self.params.mesh.origin.tolist(),
                -1 * self.params.mesh.rotation[0],
            )

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

        elif self.factory_type in ["fem", "magnetotellurics", "tipper"]:
            args.append(receivers)
            args.append(frequency)

        elif self.factory_type in ["tdem"]:
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
            kwargs = dict(
                zip(
                    ["amplitude", "inclination", "declination"],
                    self.params.inducing_field_aid(),
                    strict=False,
                )
            )
        if self.factory_type in ["magnetotellurics", "tipper"]:
            background = deepcopy(self.params.background_conductivity)

            if getattr(self.params, "model_type", None) == "Resistivity (Ohm-m)":
                background **= -1.0

            kwargs["sigma_primary"] = [background]

        if self.factory_type in ["fem"]:
            kwargs["location"] = locations
        if self.factory_type in ["tdem"]:
            kwargs["location"] = locations
            kwargs["waveform"] = waveform

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
            if "direct current" in self.factory_type:
                from simpeg.electromagnetics.static.resistivity import sources
            else:
                from simpeg.electromagnetics.static.induced_polarization import sources
            self.simpeg_object = sources.Pole
        else:
            args.append(locations_b)

        return args
