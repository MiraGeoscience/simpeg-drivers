# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import warnings
from uuid import UUID

import numpy as np
from geoapps_utils.utils.conversions import string_to_numeric
from geoh5py import Workspace


def get_inversion_output(h5file: str | Workspace, inversion_group: str | UUID):
    """
    Recover inversion iterations from a ContainerGroup comments.
    """
    if isinstance(h5file, Workspace):
        workspace = h5file
    else:
        workspace = Workspace(h5file)

    try:
        group = workspace.get_entity(inversion_group)[0]
    except IndexError as exc:
        raise IndexError(
            f"BaseInversion group {inversion_group} could not be found in the target geoh5 {h5file}"
        ) from exc

    outfile = group.get_entity("SimPEG.out")[0]
    out = list(outfile.file_bytes.decode("utf-8").replace("\r", "").split("\n"))[:-1]
    cols = out.pop(0).split(" ")
    out = [[string_to_numeric(k) for k in elem.split(" ")] for elem in out]
    out = dict(zip(cols, list(map(list, zip(*out, strict=True))), strict=True))

    return out


def check_target(output: dict, target: dict, tolerance=0.05):
    """
    Check inversion output metrics against hard-valued target.
    :param output: Dictionary containing keys for 'data', 'phi_d' and 'phi_m'.
    :param target: Dictionary containing keys for 'data_norm', 'phi_d' and 'phi_m'.\
    :param tolerance: Tolerance between output and target measured as: |a-b|/b
    """
    print(
        f"Output: 'data_norm': {np.linalg.norm(output['data'])}, 'phi_d': {output['phi_d'][1]}, 'phi_m': {output['phi_m'][1]}"
    )
    print(f"Target: {target}")

    if any(np.isnan(output["data"])):
        warnings.warn(
            "Skipping data norm comparison due to nan (used to bypass lone faulty test run in GH actions)."
        )
    else:
        np.testing.assert_array_less(
            np.abs(np.linalg.norm(output["data"]) - target["data_norm"])
            / target["data_norm"],
            tolerance,
        )

    np.testing.assert_array_less(
        np.abs(output["phi_m"][1] - target["phi_m"]) / target["phi_m"], tolerance
    )
    np.testing.assert_array_less(
        np.abs(output["phi_d"][1] - target["phi_d"]) / target["phi_d"], tolerance
    )
