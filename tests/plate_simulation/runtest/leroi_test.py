# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import subprocess


def test_leroi_executable(tmp_path):
    control_file = tmp_path / "test.cfl"
    control_file.touch()
    subprocess.run("F2.bat test output", cwd=tmp_path, shell=True, check=False)


def test_leroi_run(tmp_path):
