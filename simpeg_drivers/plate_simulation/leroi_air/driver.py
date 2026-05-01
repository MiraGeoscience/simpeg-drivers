# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import subprocess
from pathlib import Path

from .interface import LeroiAirInterface
from .options import LeroiAirOptions


class LeroiAirDriver:
    """Orchestrates a LeroiAir forward simulation from input preparation to geoh5 output."""

    def __init__(
        self,
        options: LeroiAirOptions,
    ) -> None:
        """Initialize with simulation options."""
        self.options = options
        self.interface = LeroiAirInterface(options)

    @property
    def project_path(self) -> Path:
        """Directory containing the geoh5 workspace file."""
        return self.options.survey.entity.workspace.h5file.parent

    def run_leroi(self) -> subprocess.CompletedProcess:
        """Run the LeroiAir executable and raise on non-zero exit."""
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
        return result

    def run(self) -> None:
        """Write input, run LeroiAir, and save simulated data to geoh5."""
        self.interface.input.write_cfl_file(self.project_path / "LeroiAir.cfl")
        self.run_leroi()
        self.interface.output.save_to_geoh5(
            outfile=self.project_path / "LeroiAir.out",
            out_group=self.options.out_group,
            normalization=1e-9,
        )
