# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                     '
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
#
#  This file is part of python-training.

import os
import sys
from pathlib import Path

CONVERT = {"ipynb": ".py", "py": ".ipynb"}


def update_files(ext):
    doc_path = Path(__file__).parent.parent / "docs"
    for directory, _, files in os.walk(doc_path):
        if (
            ".ipynb_checkpoints" in directory
            or "_build" in directory
            or "__pycache__" in directory
        ):
            continue

        for file in files:
            path = Path(file)

            if path.suffix != CONVERT[ext] or "__init__" in file:
                continue

            os.system(
                f"jupytext --output {Path(directory) / (path.stem + '.' + ext)} {Path(directory) / path}"
            )


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] not in ["py", "ipynb"]:
        raise UserWarning("Input argument should be one of 'py' or 'ipynb'.")

    ext = sys.argv[1]

    update_files(ext)
