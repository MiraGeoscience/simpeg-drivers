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

from pathlib import Path
from typing import ClassVar

from geoh5py.data import FloatData

from simpeg_drivers import assets_path
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions


class IP3DForwardOptions(BaseForwardOptions):
    """
    Induced Polarization 3D forward options.

    :param chargeability_channel_bool: Chargeability channel boolean.
    :param conductivity_model: Conductivity model.
    """

    name: ClassVar[str] = "Induced Polarization 3D Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_3d_forward.ui.json"
    )

    title: str = "Induced Polarization 3D Forward"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization 3d"

    chargeability_channel_bool: bool = True
    model_type: str = "Conductivity (S/m)"
    conductivity_model: float | FloatData


class IP3DInversionOptions(BaseInversionOptions):
    """
    Induced Polarization 3D inversion options.

    :param chargeability_channel: Chargeability data channel.
    :param chargeability_uncertainty: Chargeability data uncertainty channel.
    :param conductivity_model: Conductivity model.
    """

    name: ClassVar[str] = "Induced Polarization 3D Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/induced_polarization_3d_inversion.ui.json"
    )

    title: str = "Induced Polarization 3D Inversion"
    physical_property: str = "chargeability"
    inversion_type: str = "induced polarization 3d"

    chargeability_channel: FloatData
    chargeability_uncertainty: float | FloatData | None = None
    model_type: str = "Conductivity (S/m)"
    conductivity_model: float | FloatData
    lower_bound: float | FloatData | None = 0.0
