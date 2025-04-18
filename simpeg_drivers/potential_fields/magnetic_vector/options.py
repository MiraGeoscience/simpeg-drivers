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
from geoh5py.ui_json.annotations import Deprecated
from pydantic import model_validator

from simpeg_drivers import assets_path
from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions


class MVIForwardOptions(BaseForwardOptions):
    """
    Magnetic Vector forward options.

    :param tmi_channel_bool: Total magnetic intensity channel boolean.
    :param bx_channel_bool: Bx channel boolean.
    :param by_channel_bool: By channel boolean.
    :param bz_channel_bool: Bz channel boolean.
    :param bxx_channel_bool: Bxx channel boolean.
    :param bxy_channel_bool: Bxy channel boolean.
    :param bxz_channel_bool: Bxz channel boolean.
    :param byy_channel_bool: Byy channel boolean.
    :param byz_channel_bool: Byz channel boolean.
    :param bzz_channel_bool: Bzz channel boolean.
    """

    name: ClassVar[str] = "Magnetic Vector Forward"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetic_vector_forward.ui.json"
    )

    title: str = "Magnetic Vector Forward"
    physical_property: str = "susceptibility"
    inversion_type: str = "magnetic vector"

    tmi_channel_bool: bool = True
    bx_channel_bool: bool = False
    by_channel_bool: bool = False
    bz_channel_bool: bool = False
    bxx_channel_bool: bool = False
    bxy_channel_bool: bool = False
    bxz_channel_bool: bool = False
    byy_channel_bool: bool = False
    byz_channel_bool: bool = False
    bzz_channel_bool: bool = False
    inducing_field_strength: float | FloatData = 50000.0
    inducing_field_inclination: float | FloatData = 90.0
    inducing_field_declination: float | FloatData = 0.0
    starting_inclination: float | FloatData | None = None
    starting_declination: float | FloatData | None = None


class MVIInversionOptions(BaseInversionOptions):
    """
    Magnetic Vector Inversion options.

    :param tmi_channel: Total magnetic intensity channel.
    :param bx_channel: Bx channel.
    :param by_channel: By channel.
    :param bz_channel: Bz channel.
    :param bxx_channel: Bxx channel.
    :param bxy_channel: Bxy channel.
    :param bxz_channel: Bxz channel.
    :param byy_channel: Byy channel.
    :param byz_channel: Byz channel.
    :param bzz_channel: Bzz channel.
    :param tmi_uncertainty: Total magnetic intensity uncertainty.
    :param bx_uncertainty: Bx uncertainty.
    :param by_uncertainty: By uncertainty.
    :param bz_uncertainty: Bz uncertainty.
    :param bxx_uncertainty: Bxx uncertainty.
    :param bxy_uncertainty: Bxy uncertainty.
    :param bxz_uncertainty: Bxz uncertainty.
    :param byy_uncertainty: Byy uncertainty.
    :param byz_uncertainty: Byz uncertainty.
    :param bzz_uncertainty: Bzz uncertainty.
    :param inducing_field_strength: Inducing field strength.
    :param inducing_field_inclination: Inducing field inclination.
    :param inducing_field_declination: Inducing field declination.
    :param starting_inclination: Starting inclination.
    :param starting_declination: Starting declination.
    :param reference_inclination: Reference inclination.
    :param reference_declination: Reference declination.
    """

    name: ClassVar[str] = "Magnetic Vector Inversion"
    default_ui_json: ClassVar[Path] = (
        assets_path() / "uijson/magnetic_vector_inversion.ui.json"
    )

    title: str = "Magnetic Vector Inversion"
    physical_property: str = "susceptibility"
    inversion_type: str = "magnetic vector"

    tmi_channel: FloatData | None = None
    bx_channel: FloatData | None = None
    by_channel: FloatData | None = None
    bz_channel: FloatData | None = None
    bxx_channel: FloatData | None = None
    bxy_channel: FloatData | None = None
    bxz_channel: FloatData | None = None
    byy_channel: FloatData | None = None
    byz_channel: FloatData | None = None
    bzz_channel: FloatData | None = None
    tmi_uncertainty: float | FloatData | None = None
    bx_uncertainty: float | FloatData | None = None
    by_uncertainty: float | FloatData | None = None
    bz_uncertainty: float | FloatData | None = None
    bxx_uncertainty: float | FloatData | None = None
    bxy_uncertainty: float | FloatData | None = None
    bxz_uncertainty: float | FloatData | None = None
    byy_uncertainty: float | FloatData | None = None
    byz_uncertainty: float | FloatData | None = None
    bzz_uncertainty: float | FloatData | None = None
    inducing_field_strength: float | FloatData = 50000.0
    inducing_field_inclination: float | FloatData = 90.0
    inducing_field_declination: float | FloatData = 0.0

    lower_bound: Deprecated | None = None

    starting_inclination: float | FloatData | None = None
    starting_declination: float | FloatData | None = None
    reference_inclination: float | FloatData | None = None
    reference_declination: float | FloatData | None = None
