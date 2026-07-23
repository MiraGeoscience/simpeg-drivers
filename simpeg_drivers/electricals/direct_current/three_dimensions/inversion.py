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

import numpy as np

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.electricals.direct_current.three_dimensions.options import (
    DC3DInversionOptions,
)
from simpeg_drivers.utils.utils import argument_parser


class DC3DInversionDriver(InversionDriver):
    """Direct Current 3D inversion driver."""

    _params_class = DC3DInversionOptions

    def split_list(self, tiles: list[np.ndarray]) -> list[list[np.ndarray]]:
        """
        Overloaded method with optimization of source/receivers per tile.

        :param tiles: List of arrays defining tiles

        :return: New list with more even split
        """
        split_list = [1] * len(tiles)

        while True:
            populations = []
            for tile, split in zip(tiles, split_list, strict=True):
                populations.append(len(tile) // split)

            low, high = np.min(populations), np.max(populations)

            if ((high - low) / low) < 0.25:
                break

            split_list[np.argmax(populations)] += 1

        flat_tile_list = []
        for tile, split in zip(tiles, split_list, strict=True):
            flat_tile_list += [
                sub for sub in np.array_split(tile, split) if len(sub) > 0
            ]

        return super().split_list(flat_tile_list)


if __name__ == "__main__":
    file, args = argument_parser()
    DC3DInversionDriver.start_dask_run(file, **args)
