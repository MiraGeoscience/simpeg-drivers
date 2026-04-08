# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True, scope="session")
def conda_scripts_on_path():
    """Ensure the conda env Scripts directory is on PATH.
    PyCharm (and other IDEs) launch pytest with the configured Python interpreter
    but do not fully activate the conda environment, so the interpreter's sibling
    Scripts/ directory is absent from PATH.  This fixture adds it once per session
    so that subprocess calls to executables installed there (e.g. LeroiAir550_JR)
    resolve correctly without hard-coding any paths in the tests themselves.
    """
    scripts_dir = str(Path(sys.executable).parent / "Scripts")
    original_path = os.environ.get("PATH", "")
    if scripts_dir not in original_path.split(os.pathsep):
        os.environ["PATH"] = scripts_dir + os.pathsep + original_path
    yield
    os.environ["PATH"] = original_path
