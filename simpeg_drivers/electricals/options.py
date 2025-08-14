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

from pydantic import BaseModel


class FileControlOptions(BaseModel):
    """
    File control parameters for pseudo 3D simulations.

    :param files_only: Boolean to only write files.
    :param cleanup: Boolean to cleanup files.
    """

    files_only: bool = False
    cleanup: bool = True
