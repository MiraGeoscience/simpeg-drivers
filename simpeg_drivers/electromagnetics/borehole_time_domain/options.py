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

    :param a_channel_bool: In-line (A) data channel boolean.
    :param u_channel_bool: Vertical (U) data channel boolean.
    :param v_channel_bool: Cross-line (V) data channel boolean.
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
    a_channel_bool: bool = False
    u_channel_bool: bool = False
    v_channel_bool: bool = False

    models: ConductivityModelOptions


class BoreholeTDEMInversionOptions(BaseTDEMOptions, BaseInversionOptions):
    """
    Time Domain Electromagnetic Inversion options for borehole surveys.

    :param u_channel: Vertical (U) component data channel.
    :param u_uncertainty: Vertical (U) component data channel uncertainty.
    :param a_channel: In-line (A) data channel.
    :param a_uncertainty: In-line (A) data channel uncertainty.
    :param v_channel: Cross-line (V) data channel.
    :param v_uncertainty: Cross-line(V) data channel uncertainty.
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
    a_channel: PropertyGroup | None = None
    a_uncertainty: PropertyGroup | None = None
    u_channel: PropertyGroup | None = None
    u_uncertainty: PropertyGroup | None = None
    v_channel: PropertyGroup | None = None
    v_uncertainty: PropertyGroup | None = None

    models: ConductivityModelOptions
