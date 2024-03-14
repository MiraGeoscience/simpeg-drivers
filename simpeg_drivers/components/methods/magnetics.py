#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from SimPEG.maps import IdentityMap
from SimPEG.potential_fields.magnetics import receivers, simulation, sources, survey

from .base import SimPEGMisfit, SimPEGSimulation, SimPEGSurvey

if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver


class PotentialFieldSurvey(SimPEGSurvey):
    """
    Build SimPEG survey objects based on factory type.
    """

    @classmethod
    def build(cls, driver: InversionDriver, local_index: np.ndarray, **_):
        """
        Generate a concrete SimPEG survey from input.
        """
        receiver_class = cls.create_receivers(driver, local_index)
        background_source = cls.create_sources(driver, receiver_class)
        return cls._class_type(background_source)

    @classmethod
    def create_receivers(cls, driver, local_index, **_):
        locations = driver.inversion_data.locations[local_index]

        return cls._receiver_type(
            locations,
            components=list(driver.inversion_data.observed),
        )

    @classmethod
    def create_sources(cls, driver, receiver_class, **_):
        kwargs = dict(
            zip(
                ["amplitude", "inclination", "declination"],
                driver.params.inducing_field_aid(),
            )
        )
        return cls._source_type(receiver_class, **kwargs)


class MagneticSurvey(PotentialFieldSurvey):
    _class_type = survey.Survey
    _receiver_type: type = receivers.Point
    _source_type: type = sources.UniformBackgroundField


class MagneticScalarSimulation(SimPEGSimulation):
    _class_type = simulation.Simulation3DIntegral

    def build(self) -> simulation.Simulation3DIntegral:
        mapping = IdentityMap(nP=self.n_values)

        return self._class_type(
            self.mesh,
            ind_active=self.active_cells,
            chiMap=mapping,
            sensitivity_path=self._get_sensitivity_path(),
        )


class MagneticScalarMisfit(SimPEGMisfit):
    _simulation_factory = MagneticScalarSimulation
    _survey_factory = MagneticSurvey

    def _get_data(self) -> tuple[np.ndarray, np.ndarray]:
        local_data = {
            k: v[self.indices] for k, v in self.driver.inversion_data.observed.items()
        }
        local_uncertainties = {
            k: v[self.indices]
            for k, v in self.driver.inversion_data.uncertainties.items()
        }

        data_vec = self._stack_channels(local_data, "column")
        uncertainty_vec = self._stack_channels(local_uncertainties, "column")
        uncertainty_vec[np.isnan(data_vec)] = np.inf
        data_vec[np.isnan(data_vec)] = self.dummy  # Nan's handled by inf uncertainties
        return data_vec, uncertainty_vec
