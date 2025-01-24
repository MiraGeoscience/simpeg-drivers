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


__version__ = "0.3.0-alpha.1"


import logging
from pathlib import Path

from simpeg_drivers.constants import default_ui_json


# from simpeg_drivers.params import InversionBaseParams


logging.basicConfig(level=logging.INFO)

__all__ = [
    "DRIVER_MAP",
    "InversionBaseParams",
    "assets_path",
    "default_ui_json",
]


def assets_path() -> Path:
    """Return the path to the assets folder."""

    parent = Path(__file__).parent
    folder_name = f"{parent.name}-assets"
    assets_folder = parent.parent / folder_name
    if not assets_folder.is_dir():
        raise RuntimeError(f"Assets folder not found: {assets_folder}")

    return assets_folder


DRIVER_MAP = {
    "direct current 3d": (
        "simpeg_drivers.electricals.direct_current.three_dimensions.driver",
        {"inversion": "DirectCurrent3DDriver"},
    ),
    "direct current 2d": (
        "simpeg_drivers.electricals.direct_current.two_dimensions.driver",
        {"inversion": "DirectCurrent2DDriver"},
    ),
    "direct current pseudo 3d": (
        "simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.driver",
        {"inversion": "DirectCurrentPseudo3DDriver"},
    ),
    "induced polarization 3d": (
        "simpeg_drivers.electricals.induced_polarization.three_dimensions.driver",
        {"inversion": "InducedPolarization3DDriver"},
    ),
    "induced polarization 2d": (
        "simpeg_drivers.electricals.induced_polarization.two_dimensions.driver",
        {"inversion": "InducedPolarization2DDriver"},
    ),
    "induced polarization pseudo 3d": (
        "simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.driver",
        {"inversion": "InducedPolarizationPseudo3DDriver"},
    ),
    "joint surveys": (
        "simpeg_drivers.joint.joint_surveys.driver",
        {"inversion": "JointSurveyDriver"},
    ),
    "fem": (
        "simpeg_drivers.electromagnetics.frequency_domain.driver",
        {"inversion": "FrequencyDomainElectromagneticsDriver"},
    ),
    "joint cross gradient": (
        "simpeg_drivers.joint.joint_cross_gradient.driver",
        {"inversion": "JointCrossGradientDriver"},
    ),
    "tdem": (
        "simpeg_drivers.electromagnetics.time_domain.driver",
        {"inversion": "TimeDomainElectromagneticsDriver"},
    ),
    "magnetotellurics": (
        "simpeg_drivers.natural_sources.magnetotellurics.driver",
        {"inversion": "MagnetotelluricsDriver"},
    ),
    "tipper": (
        "simpeg_drivers.natural_sources.tipper.driver",
        {"inversion": "TipperDriver"},
    ),
    "gravity": (
        "simpeg_drivers.potential_fields.gravity.driver",
        {"inversion": "GravityInversionDriver", "forward": "GravityForwardDriver"},
    ),
    "magnetic scalar": (
        "simpeg_drivers.potential_fields.magnetic_scalar.driver",
        {"inversion": "MagneticScalarDriver"},
    ),
    "magnetic vector": (
        "simpeg_drivers.potential_fields.magnetic_vector.driver",
        {"inversion": "MagneticVectorDriver"},
    ),
}
