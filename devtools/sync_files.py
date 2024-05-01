#  Copyright (c) 2024 Mira Geoscience Ltd.
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
