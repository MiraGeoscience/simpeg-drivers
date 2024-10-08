# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.
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
import sys
from pathlib import Path

from geoapps_utils.driver.data import BaseData
from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile


def tile_estimator(file_path: Path):
    """
    Estimate the number of tiles required to process a large file.
    """
    ifile = InputFile.read_ui_json(file_path)
    params = parameters.build(ifile)

    print(f"Estimated number of tiles: {params.max_tiles}")


class parameters(BaseData):
    """
    Parameters for the tile estimator.
    """

    simulation: SimPEGGroup
    max_tiles: int


if __name__ == "__main__":
    file = str(Path(sys.argv[1]).resolve())
    tile_estimator(file)
    sys.stdout.close()
