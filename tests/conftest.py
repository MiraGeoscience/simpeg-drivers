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

#
#  This file is part of simpeg-drivers.
#
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#
#  This file is part of simpeg-drivers.
#
#  simpeg-drivers is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

from pathlib import Path

import pytest
import tomli as toml


@pytest.fixture
def pyproject() -> dict[str]:
    """Return the pyproject.toml as a dictionary."""

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as pyproject_file:
        return toml.load(pyproject_file)
