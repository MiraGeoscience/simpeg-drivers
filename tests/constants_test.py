# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024-2025 Mira Geoscience Ltd.                                '
#  All rights reserved.                                                        '
#                                                                              '
#  This file is part of simpeg-drivers.                                        '
#                                                                              '
#  The software and information contained herein are proprietary to, and       '
#  comprise valuable trade secrets of, Mira Geoscience, which                  '
#  intend to preserve as trade secrets such software and information.          '
#  This software is furnished pursuant to a written license agreement and      '
#  may be used, copied, transmitted, and stored only in accordance with        '
#  the terms of such license and with the inclusion of the above copyright     '
#  notice.  This software and information or any other copies thereof may      '
#  not be provided or otherwise made available to any other person.            '
#                                                                              '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

from simpeg_drivers.electricals.direct_current.three_dimensions import (
    constants as direct_current_constants,
)
from simpeg_drivers.electricals.induced_polarization.three_dimensions import (
    constants as induced_polarization_constants,
)
from simpeg_drivers.potential_fields.gravity import constants as gravity_constants
from simpeg_drivers.potential_fields.magnetic_scalar import (
    constants as magnetic_scalar_constants,
)
from simpeg_drivers.potential_fields.magnetic_vector import (
    constants as magnetic_vector_constants,
)


constants = [
    gravity_constants,
    magnetic_scalar_constants,
    magnetic_vector_constants,
    direct_current_constants,
    induced_polarization_constants,
]


def test_deprecated_uijson_fields():
    deprecated_fields = ["default"]
    for constant in constants:
        d_u_j = constant.default_ui_json
        for value in d_u_j.values():
            if isinstance(value, dict):
                for field in deprecated_fields:
                    assert field not in value.keys()
