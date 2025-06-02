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
from typing import ClassVar, TypeAlias

from geoh5py.groups import PropertyGroup
from geoh5py.objects import (
    AirborneTEMReceivers,
    LargeLoopGroundTEMReceivers,
    MovingLoopGroundTEMReceivers,
)

from simpeg_drivers import assets_path
from simpeg_drivers.electromagnetics.time_domain.options import BaseTDEMOptions
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    DrapeModelOptions,
    EMDataMixin,
)


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class TDEM1DForwardOptions(BaseTDEMOptions, BaseForwardOptions):
    """
    Time Domain Electromagnetic forward options.

    :param z_channel_bool: Z-component data channel boolean.
    :param x_channel_bool: X-component data channel boolean.
    :param y_channel_bool: Y-component data channel boolean.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_forward.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Forward"
    inversion_type: str = "tdem 1d"

    z_channel_bool: bool

    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )


class TDEM1DInversionOptions(BaseTDEMOptions, BaseInversionOptions):
    """
    Time Domain Electromagnetic Inversion options.

    :param z_channel: Z-component data channel.
    :param z_uncertainty: Z-component data channel uncertainty.
    :param x_channel: X-component data channel.
    :param x_uncertainty: X-component data channel uncertainty.
    :param y_channel: Y-component data channel.
    :param y_uncertainty: Y-component data channel uncertainty.
    :param model_type: Specify whether the models are provided in resistivity or conductivity.
    :param data_units: Units for the TEM data
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_inversion.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Inversion"
    inversion_type: str = "tdem 1d"

    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None
    length_scale_y: None = None
    y_norm: None = None

    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )
    auto_scale_misfits: bool = False
    sens_wts_threshold: float = 100.0
