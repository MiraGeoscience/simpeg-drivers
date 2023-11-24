#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.
#

from my_app import assets_path


def test_assets_directory_exist():
    assert assets_path().is_dir()


def test_uijson_files_exists():
    assert (assets_path() / "uijson").is_dir()
    assert list((assets_path() / "uijson").iterdir())[0].is_file()
