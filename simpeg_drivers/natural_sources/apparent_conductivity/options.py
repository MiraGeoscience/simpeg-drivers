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

from geoh5py.data import FloatData
from geoh5py.groups import PropertyGroup
from geoh5py.objects import AirborneAppConReceivers

from simpeg_drivers import assets_path
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
    ConductivityModelOptions,
    EMDataMixin,
)


class AppConForwardOptions(EMDataMixin, BaseForwardOptions):
    """
    AppCon forward options.
    """

    name: ClassVar[str] = "Apparent Conductivity Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/apparent_conductivity_forward.ui.json"
    )

    title: str = "Apparent Conductivity Forward"
    physical_property: str = "conductivity"
    inversion_type: str = "apparent conductivity"
    app_con_channel_bool: bool = True
    data_object: AirborneAppConReceivers
    models: ConductivityModelOptions


class AppConInversionOptions(EMDataMixin, BaseInversionOptions):
    """
    AppCon Inversion options.

    :param app_con_channel: Apparent conductivity data.
    :param app_con_uncertainty: Apparent conductivity uncertainties.
    """

    name: ClassVar[str] = "Apparent Conductivity Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/apparent_conductivity_inversion.ui.json"
    )

    title: str = "Apparent Conductivity Inversion"
    physical_property: str = "conductivity"
    inversion_type: str = "apparent conductivity"

    data_object: AirborneAppConReceivers
    app_con_channel: PropertyGroup
    app_con_uncertainty: PropertyGroup
    models: ConductivityModelOptions
