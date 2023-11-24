#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.

from __future__ import annotations

__version__ = "0.1.0-alpha.1"

from pathlib import Path


def assets_path() -> Path:
    """Return the path to the assets folder."""

    parent = Path(__file__).parent
    folder_name = f"{parent.name}-assets"
    assets_folder = parent.parent / folder_name
    if not assets_folder.is_dir():
        raise RuntimeError(f"Assets folder not found: {assets_folder}")

    return assets_folder
