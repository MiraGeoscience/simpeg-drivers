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
from simpeg_drivers.electromagnetics.time_domain.options import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)
from simpeg_drivers.options import (
    DirectiveOptions,
    DrapeModelOptions,
)


Receivers: TypeAlias = (
    MovingLoopGroundTEMReceivers | LargeLoopGroundTEMReceivers | AirborneTEMReceivers
)


class TDEM1DForwardOptions(TDEMForwardOptions):
    """
    Time Domain Electromagnetic forward options.

    :param z_channel_bool: Z-component data channel boolean.
    :param drape_model: Options for drape mesh.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Forward"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_forward.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Forward"
    inversion_type: str = "tdem 1d"

    z_channel_bool: bool = True

    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )


class TDEM1DInversionOptions(TDEMInversionOptions):
    """
    Time Domain Electromagnetic Inversion options.

    :param z_channel: Z-component data channel.
    :param z_uncertainty: Z-component data channel uncertainty.
    :param drape_model: Options for drape mesh.
    """

    name: ClassVar[str] = "Time Domain Electromagnetics Inversion"
    default_ui_json: ClassVar[Path] = assets_path() / "uijson/tdem1d_inversion.ui.json"

    title: str = "Time-domain EM-1D (TEM-1D) Inversion"
    inversion_type: str = "tdem 1d"

    z_channel: PropertyGroup | None = None
    z_uncertainty: PropertyGroup | None = None

    directives: DirectiveOptions = DirectiveOptions(
        sens_wts_threshold=100.0,
    )
    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )
