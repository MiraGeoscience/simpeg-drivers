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

from pydantic import BaseModel, ConfigDict

from simpeg_drivers.options import DrapeModelOptions


class Base1DOptions(BaseModel):
    """
    Frequency Domain Electromagnetic forward options.

    :param drape_model: Drape model options.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    drape_model: DrapeModelOptions = DrapeModelOptions(
        u_cell_size=10.0,
        v_cell_size=10.0,
        depth_core=100.0,
        horizontal_padding=0.0,
        vertical_padding=100.0,
        expansion_factor=1.1,
    )
