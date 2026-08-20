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
    ConductivityModelOptions,
)


class BoreholeTDEMForwardOptions(BaseTDEMOptions, BaseForwardOptions):
    """
    Time Domain Electromagnetic forward options for borehole surveys.

    :param A_channel_bool: In-line (A) data channel boolean.
    :param U_channel_bool: Vertical (U) data channel boolean.
    :param V_channel_bool: Cross-line (V) data channel boolean.
    """

    name: ClassVar[str] = "Borehole TDEM Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/borehole_tdem_forward.ui.json"
    )
    run_command: str = "simpeg_drivers.electromagnetics.borehole_time_domain.forward"

    title: str = "Borehole TDEM Forward"
    icon: str = "surveyairborneem"
    inversion_type: str = "borehole tdem"
    physical_property: str = "conductivity"

    data_object: (
        MovingLoopGroundTEMReceivers
        | LargeLoopGroundTEMReceivers
        | AirborneTEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
    A_channel_bool: bool = False
    U_channel_bool: bool = False
    V_channel_bool: bool = False

    models: ConductivityModelOptions


class BoreholeTDEMInversionOptions(BaseTDEMOptions, BaseInversionOptions):
    """
    Time Domain Electromagnetic Inversion options for borehole surveys.

    :param U_channel: Vertical (U) component data channel.
    :param U_uncertainty: Vertical (U) component data channel uncertainty.
    :param A_channel: In-line (A) data channel.
    :param A_uncertainty: In-line (A) data channel uncertainty.
    :param V_channel: Cross-line (V) data channel.
    :param V_uncertainty: Cross-line(V) data channel uncertainty.
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

    data_object: (
        MovingLoopGroundTEMReceivers
        | LargeLoopGroundTEMReceivers
        | AirborneTEMReceivers
    )
    receivers_orientation: PropertyGroup | None = None
    U_channel: PropertyGroup | None = None
    U_uncertainty: PropertyGroup | None = None
    A_channel: PropertyGroup | None = None
    A_uncertainty: PropertyGroup | None = None
    V_channel: PropertyGroup | None = None
    V_uncertainty: PropertyGroup | None = None

    models: ConductivityModelOptions
