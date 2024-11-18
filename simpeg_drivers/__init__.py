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


__version__ = "0.2.0-beta.2"


import logging
from pathlib import Path

from simpeg_drivers.constants import default_ui_json
from simpeg_drivers.params import InversionBaseParams


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
        "DirectCurrent3DDriver",
    ),
    "direct current 2d": (
        "simpeg_drivers.electricals.direct_current.two_dimensions.driver",
        "DirectCurrent2DDriver",
    ),
    "direct current pseudo 3d": (
        "simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.driver",
        "DirectCurrentPseudo3DDriver",
    ),
    "induced polarization 3d": (
        "simpeg_drivers.electricals.induced_polarization.three_dimensions.driver",
        "InducedPolarization3DDriver",
    ),
    "induced polarization 2d": (
        "simpeg_drivers.electricals.induced_polarization.two_dimensions.driver",
        "InducedPolarization2DDriver",
    ),
    "induced polarization pseudo 3d": (
        "simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.driver",
        "InducedPolarizationPseudo3DDriver",
    ),
    "joint surveys": (
        "simpeg_drivers.joint.joint_surveys.driver",
        "JointSurveyDriver",
    ),
    "fem": (
        "simpeg_drivers.electromagnetics.frequency_domain.driver",
        "FrequencyDomainElectromagneticsDriver",
    ),
    "joint cross gradient": (
        "simpeg_drivers.joint.joint_cross_gradient.driver",
        "JointCrossGradientDriver",
    ),
    "tdem": (
        "simpeg_drivers.electromagnetics.time_domain.driver",
        "TimeDomainElectromagneticsDriver",
    ),
    "magnetotellurics": (
        "simpeg_drivers.natural_sources.magnetotellurics.driver",
        "MagnetotelluricsDriver",
    ),
    "tipper": ("simpeg_drivers.natural_sources.tipper.driver", "TipperDriver"),
    "gravity": ("simpeg_drivers.potential_fields.gravity.driver", "GravityDriver"),
    "magnetic scalar": (
        "simpeg_drivers.potential_fields.magnetic_scalar.driver",
        "MagneticScalarDriver",
    ),
    "magnetic vector": (
        "simpeg_drivers.potential_fields.magnetic_vector.driver",
        "MagneticVectorDriver",
    ),
}
