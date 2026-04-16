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
from pathlib import Path

from geoh5py.groups import UIJsonGroup

from .interface import LeroiAirInterface
from .options import LeroiAirOptions


class LeroiAirDriver:
    def __init__(self, options: LeroiAirOptions):
        self.options = options
        self._interface: LeroiAirInterface | None = None
        self.out_group: UIJsonGroup | None = None

    @property
    def interface(self) -> LeroiAirInterface:
        if self._interface is None:
            self._interface = LeroiAirInterface(self.options)
        return self._interface

    @property
    def project_path(self) -> Path:
        return self.options.survey.workspace.h5file.parent

    def run(self):
        self.interface.write_cfl_file(self.project_path / "LeroiAir.cfl")

        result = subprocess.run(
            ["LeroiAir550_JR", "LeroiAir"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"LeroiAir failed with return code {result.returncode}.\n"
                f"stderr:\n{result.stderr}\n"
                f"stdout:\n{result.stdout}"
            )

        outfile = self.project_path / "LeroiAir.out"
        self.interface.save_to_geoh5(
            outfile=outfile,
            out_group=self.out_group,
        )
