#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from geoapps_utils.transformations import rotate_xyz
from geoh5py.objects import LargeLoopGroundTEMReceivers
from SimPEG.electromagnetics.frequency_domain import sources as fem_sources
from SimPEG.electromagnetics.natural_source import sources as ns_sources
from SimPEG.electromagnetics.static.induced_polarization import sources as ip_sources
from SimPEG.electromagnetics.static.resistivity import sources as res_sources
from SimPEG.electromagnetics.time_domain import sources as tem_sources
from SimPEG.potential_fields.gravity import sources as grav_sources
from SimPEG.potential_fields.magnetics import sources as mag_sources

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory

if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

SOURCES = {
    "magnetic scalar": mag_sources.UniformBackgroundField,
    "magnetic vector": mag_sources.UniformBackgroundField,
    "gravity": grav_sources.SourceField,
    "direct current 2d": res_sources.Dipole,
    "direct current 3d": res_sources.Dipole,
    "direct current pseudo 3d": res_sources.Dipole,
    "induced polarization 2d": ip_sources.Dipole,
    "induced polarization 3d": ip_sources.Dipole,
    "induced polarization pseudo 3d": ip_sources.Dipole,
    "fem": fem_sources.MagDipole,
    "tdem": tem_sources.MagDipole,
    "magnetotellurics": ns_sources.PlanewaveXYPrimary,
    "tipper": ns_sources.PlanewaveXYPrimary,
}


class SourcesFactory(SimPEGFactory):
    """Build SimPEG sources objects based on factory type."""

    def __init__(self, params: BaseParams):
        """
        :param params: Params object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

    def concrete_object(self):
        if "tdem" in self.factory_type and isinstance(
            self.params.data_object, LargeLoopGroundTEMReceivers
        ):
            return tem_sources.LineCurrent

        return SOURCES[self.factory_type]

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
                )
            )
        if self.factory_type in ["magnetotellurics", "tipper"]:
            kwargs["sigma_primary"] = [self.params.background_conductivity]
        if self.factory_type in ["fem"]:
            kwargs["location"] = locations
        if self.factory_type in ["tdem"]:
            kwargs["location"] = locations
            kwargs["waveform"] = waveform

        return kwargs

    def build(
        self, receivers=None, locations=None, frequency=None, waveform=None, **kwargs
    ):
        return super().build(
            receivers=receivers,
            locations=locations,
            frequency=frequency,
            waveform=waveform,
            **kwargs,
        )

    def _dcip_arguments(self, receivers=None, locations=None):
        args = []

        locations_a = locations[0]
        locations_b = locations[1]
        args.append([receivers])
        args.append(locations_a)

        if np.all(locations_a == locations_b):
            if "direct current" in self.factory_type:
                self.simpeg_object = res_sources.Pole
            else:
                self.simpeg_object = ip_sources.Pole

        else:
            args.append(locations_b)

        return args
