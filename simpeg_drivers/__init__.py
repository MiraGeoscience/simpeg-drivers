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


__version__ = "0.3.0-alpha.4"


import logging
from pathlib import Path

from simpeg_drivers.constants import default_ui_json


logging.basicConfig(level=logging.INFO)

__all__ = [
    "DRIVER_MAP",
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
        {
            "forward": "DC3DForwardDriver",
            "inversion": "DC3DInversionDriver",
        },
    ),
    "direct current 2d": (
        "simpeg_drivers.electricals.direct_current.two_dimensions.driver",
        {
            "forward": "DC2DForwardDriver",
            "inversion": "DC2DInversionDriver",
        },
    ),
    "direct current pseudo 3d": (
        "simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.driver",
        {
            "forward": "DCBatch2DForwardDriver",
            "inversion": "DCBatch2DInversionDriver",
        },
    ),
    "induced polarization 3d": (
        "simpeg_drivers.electricals.induced_polarization.three_dimensions.driver",
        {
            "forward": "IP3DForwardDriver",
            "inversion": "IP3DInversionDriver",
        },
    ),
    "induced polarization 2d": (
        "simpeg_drivers.electricals.induced_polarization.two_dimensions.driver",
        {
            "forward": "IP2DForwardDriver",
            "inversion": "IP2DInversionDriver",
        },
    ),
    "induced polarization pseudo 3d": (
        "simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.driver",
        {
            "forward": "IPBatch2DForwardDriver",
            "inversion": "IPBatch2DInversionDriver",
        },
    ),
    "joint surveys": (
        "simpeg_drivers.joint.joint_surveys.driver",
        {"inversion": "JointSurveyDriver"},
    ),
    "fdem": (
        "simpeg_drivers.electromagnetics.frequency_domain.driver",
        {
            "forward": "FDEMForwardDriver",
            "inversion": "FDEMInversionDriver",
        },
    ),
    "fdem 1d": (
        "simpeg_drivers.electromagnetics.frequency_domain_1d.driver",
        {
            "forward": "FDEM1DForwardDriver",
            "inversion": "FDEM1DInversionDriver",
        },
    ),
    "joint cross gradient": (
        "simpeg_drivers.joint.joint_cross_gradient.driver",
        {"inversion": "JointCrossGradientDriver"},
    ),
    "tdem": (
        "simpeg_drivers.electromagnetics.time_domain.driver",
        {
            "forward": "TDEMForwardDriver",
            "inversion": "TDEMInversionDriver",
        },
    ),
    "tdem 1d": (
        "simpeg_drivers.electromagnetics.time_domain_1d.driver",
        {
            "forward": "TDEM1DForwardDriver",
            "inversion": "TDEM1DInversionDriver",
        },
    ),
    "magnetotellurics": (
        "simpeg_drivers.natural_sources.magnetotellurics.driver",
        {
            "forward": "MTForwardDriver",
            "inversion": "MTInversionDriver",
        },
    ),
    "tipper": (
        "simpeg_drivers.natural_sources.tipper.driver",
        {"forward": "TipperForwardDriver", "inversion": "TipperInversionDriver"},
    ),
    "gravity": (
        "simpeg_drivers.potential_fields.gravity.driver",
        {"forward": "GravityForwardDriver", "inversion": "GravityInversionDriver"},
    ),
    "magnetic scalar": (
        "simpeg_drivers.potential_fields.magnetic_scalar.driver",
        {
            "forward": "MagneticForwardDriver",
            "inversion": "MagneticInversionDriver",
        },
    ),
    "magnetic vector": (
        "simpeg_drivers.potential_fields.magnetic_vector.driver",
        {
            "forward": "MagneticForwardDriver",
            "inversion": "MVIInversionDriver",
        },
    ),
}
