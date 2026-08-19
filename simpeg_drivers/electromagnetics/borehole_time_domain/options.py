# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
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

from simpeg_drivers import assets_path
from simpeg_drivers.electromagnetics.time_domain.options import (
    TDEMForwardOptions,
    TDEMInversionOptions,
)


class BoreholeTDEMForwardOptions(TDEMForwardOptions):
    """
    Time Domain Electromagnetic forward options for borehole surveys.

    :param vertical_channel_bool: Vertical (U) data channel boolean.
    :param inline_channel_bool: In-line (A) data channel boolean.
    :param crossline_channel_bool: Cross-line (V) data channel boolean.
    """

    name: ClassVar[str] = "Borehole TDEM Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/borehole_tdem_forward.ui.json"
    )
    run_command: str = "simpeg_drivers.electromagnetics.borehole_time_domain.forward"

    title: str = "Borehole TDEM Forward"
    icon: str = "surveyairborneem"
    inversion_type: str = "borehole tdem"


class BoreholeTDEMInversionOptions(TDEMInversionOptions):
    """
    Time Domain Electromagnetic Inversion options for borehole surveys.

    :param vertical_channel: Vertical (U) component data channel.
    :param vertical_uncertainty: Vertical (U) component data channel uncertainty.
    :param inline_channel: In-line (A) data channel.
    :param inline_uncertainty: In-line (A) data channel uncertainty.
    :param crossline_channel: Cross-line (V) data channel.
    :param crossline_uncertainty: Cross-line(V) data channel uncertainty.
    """

    name: ClassVar[str] = "Borehole TDEM Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/borehole_tdem_inversion.ui.json"
    )
    run_command: str = "simpeg_drivers.electromagnetics.borehole_time_domain.inversion"
    title: str = "Borehole TDEM Inversion"
    icon: str = "surveyairborneem"
    physical_property: str = "conductivity"
    inversion_type: str = "borehole tdem"
