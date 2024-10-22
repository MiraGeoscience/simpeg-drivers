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

import argparse
from pathlib import Path

from simpeg_drivers.electricals.direct_current.pseudo_three_dimensions.params import (
    DirectCurrentPseudo3DParams,
)
from simpeg_drivers.electricals.direct_current.three_dimensions import (
    DirectCurrent3DParams,
)
from simpeg_drivers.electricals.direct_current.two_dimensions import (
    DirectCurrent2DParams,
)
from simpeg_drivers.electricals.induced_polarization.pseudo_three_dimensions.params import (
    InducedPolarizationPseudo3DParams,
)
from simpeg_drivers.electricals.induced_polarization.three_dimensions import (
    InducedPolarization3DParams,
)
from simpeg_drivers.electricals.induced_polarization.two_dimensions import (
    InducedPolarization2DParams,
)
from simpeg_drivers.electromagnetics.frequency_domain import (
    FrequencyDomainElectromagneticsParams,
)
from simpeg_drivers.electromagnetics.time_domain import TimeDomainElectromagneticsParams
from simpeg_drivers.joint.joint_cross_gradient import JointCrossGradientParams
from simpeg_drivers.joint.joint_surveys import JointSurveysParams
from simpeg_drivers.natural_sources import MagnetotelluricsParams, TipperParams
from simpeg_drivers.potential_fields import (
    GravityParams,
    MagneticScalarParams,
    MagneticVectorParams,
)


active_data_channels = [
    "z_real_channel",
    "z_imag_channel",
    "zxx_real_channel",
    "zxx_imag_channel",
    "zxy_real_channel",
    "zxy_imag_channel",
    "zyx_real_channel",
    "zyx_imag_channel",
    "zyy_real_channel",
    "zyy_imag_channel",
    "txz_real_channel",
    "txz_imag_channel",
    "tyz_real_channel",
    "tyz_imag_channel",
    "gz_channel",
    "tmi_channel",
    "z_channel",
]


def write_default_uijson(path: str | Path):
    filedict = {
        "gravity_inversion.ui.json": GravityParams(validate=False),
        "gravity_forward.ui.json": GravityParams(forward_only=True, validate=False),
        "magnetic_scalar_inversion.ui.json": MagneticScalarParams(validate=False),
        "magnetic_scalar_forward.ui.json": MagneticScalarParams(
            forward_only=True, validate=False
        ),
        "magnetic_vector_inversion.ui.json": MagneticVectorParams(validate=False),
        "magnetic_vector_forward.ui.json": MagneticVectorParams(
            forward_only=True, validate=False
        ),
        "direct_current_inversion_2d.ui.json": DirectCurrent2DParams(validate=False),
        "direct_current_forward_2d.ui.json": DirectCurrent2DParams(
            forward_only=True, validate=False
        ),
        "direct_current_inversion_3d.ui.json": DirectCurrent3DParams(validate=False),
        "direct_current_forward_3d.ui.json": DirectCurrent3DParams(
            forward_only=True, validate=False
        ),
        "direct_current_inversion_pseudo3d.ui.json": DirectCurrentPseudo3DParams(
            validate=False
        ),
        "direct_current_forward_pseudo3d.ui.json": DirectCurrentPseudo3DParams(
            forward_only=True, validate=False
        ),
        "induced_polarization_inversion_2d.ui.json": InducedPolarization2DParams(
            validate=False
        ),
        "induced_polarization_forward_2d.ui.json": InducedPolarization2DParams(
            forward_only=True, validate=False
        ),
        "induced_polarization_inversion_3d.ui.json": InducedPolarization3DParams(
            validate=False
        ),
        "induced_polarization_forward_3d.ui.json": InducedPolarization3DParams(
            forward_only=True, validate=False
        ),
        "induced_polarization_inversion_pseudo3d.ui.json": InducedPolarizationPseudo3DParams(
            validate=False
        ),
        "induced_polarization_forward_pseudo3d.ui.json": InducedPolarizationPseudo3DParams(
            forward_only=True, validate=False
        ),
        "fem_inversion.ui.json": FrequencyDomainElectromagneticsParams(
            forward_only=False, validate=False
        ),
        "fem_forward.ui.json": FrequencyDomainElectromagneticsParams(
            forward_only=True, validate=False
        ),
        "tdem_inversion.ui.json": TimeDomainElectromagneticsParams(
            forward_only=False, validate=False
        ),
        "tdem_forward.ui.json": TimeDomainElectromagneticsParams(
            forward_only=True, validate=False
        ),
        "magnetotellurics_inversion.ui.json": MagnetotelluricsParams(
            forward_only=False, validate=False
        ),
        "magnetotellurics_forward.ui.json": MagnetotelluricsParams(
            forward_only=True, validate=False
        ),
        "tipper_inversion.ui.json": TipperParams(forward_only=False, validate=False),
        "tipper_forward.ui.json": TipperParams(forward_only=True, validate=False),
        "joint_surveys_inversion.ui.json": JointSurveysParams(
            forward_only=False, validate=False
        ),
        "joint_cross_gradient_inversion.ui.json": JointCrossGradientParams(
            forward_only=False, validate=False
        ),
    }

    for filename, params in filedict.items():
        validation_options = {
            "update_enabled": (True if params.geoh5 is not None else False)
        }
        params.input_file.validation_options = validation_options
        if hasattr(params, "forward_only"):
            if params.forward_only:
                for form in params.input_file.ui_json.values():
                    if isinstance(form, dict):
                        group = form.get("group", None)
                        if group == "Data":
                            form["group"] = "Survey"
                for param in [
                    "starting_model",
                    "starting_inclination",
                    "starting_declination",
                ]:
                    if param in params.input_file.ui_json:
                        form = params.input_file.ui_json[param]

                        # Exception for forward sigma models
                        if "model_type" in params.input_file.ui_json:
                            form["label"] = "Value(s)"
                        else:
                            form["label"] = (
                                form["label"].replace("Initial ", "").capitalize()
                            )
            elif params.data_object is None:
                for channel in active_data_channels:
                    form = params.input_file.ui_json.get(channel, None)
                    if form:
                        form["enabled"] = True

        ifile = params.input_file
        ifile.validate = False
        ifile.ui_json["topography_object"]["enabled"] = True
        ifile.write_ui_json(name=filename, path=path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write defaulted ui.json files.")
    parser.add_argument(
        "path",
        type=Path,
        help="Path to folder where default ui.json files will be written.",
    )
    args = parser.parse_args()
    write_default_uijson(args.path)
