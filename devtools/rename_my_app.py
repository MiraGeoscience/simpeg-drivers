#!/usr/bin/env python3

#  Copyright (c) 2022-2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.

from __future__ import annotations

import argparse
import fnmatch
import itertools
import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

THIS_FILE = Path(__file__)
IGNORE_EXTENSIONS = [
    ".bmp",
    ".geoh5",
    ".gif",
    ".h5",
    ".ico",
    ".jpeg",
    ".jpg",
    ".png",
    ".pt",
    ".pynb",
]


def dash_to_underscore(name: str) -> str:
    return name.replace("-", "_")


def underscore_to_dash(name: str) -> str:
    return name.replace("_", "-")


def load_ignore_patterns(gitignore_path: Path) -> list[str]:
    """Load and return the list of patterns from the .gitignore file."""
    patterns = []
    with open(gitignore_path) as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


class MyAppRenamer:
    """
    Replaces 'my-app' and 'my_app' with the new name in all files
    (excluding the '.git' and assets folder, as well as some known binary file extensions).

    Also calls git mv on 'my_app' and 'my_app-assets'.
    """

    def __init__(self, newname: str):
        """:param newname: The new name to replace 'my-app' and 'my_app' with."""

        self.root = Path(__file__).parents[1]
        self.gitignore_patterns = load_ignore_patterns(self.root / ".gitignore")
        self.skip_directories = [
            self.root / ".git",
            self.root / ".conda-env",
            self.root / "my_app-assets",
        ]
        self.newname = underscore_to_dash(newname)
        self.newname_underscore = dash_to_underscore(newname)

        logger.info(f"new name={self.newname}")
        logger.info(f"new name with underscores={self.newname_underscore}")

    def replace_in_file(self, filepath: Path) -> None:
        logger.debug(f"reading {filepath} ...")
        with open(filepath, encoding="utf-8") as file:
            content: str = file.read()
            patched_content = re.sub(r"\bmy-app\b", self.newname, content)
            patched_content = re.sub(
                r"\bmy_app\b", self.newname_underscore, patched_content
            )
        if patched_content != content:
            logger.info(f"patching {filepath}")
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(patched_content)

    def replace_in_directory(self, dir: Path) -> None:
        assert dir.is_dir()

        for child in dir.iterdir():
            if self.should_skip(child):
                continue

            if child.is_dir():
                self.replace_in_directory(child)
            elif child.is_file():
                self.replace_in_file(child)

    def replace_in_assets(self) -> None:
        """Replace 'my-app' and 'my_app' in the assets folder."""
        assets_folder = self.root / "my_app-assets"
        assert assets_folder.is_dir()

        for child in itertools.chain(
            assets_folder.rglob("*.py"), assets_folder.rglob("*.json")
        ):
            asset_file = Path(child)
            assert asset_file.is_file()
            if not self.should_skip(asset_file):
                self.replace_in_file(asset_file)

    def run(self):
        """Applies the renaming across files and directories."""
        status_lines = subprocess.run(
            ["git", "status", "--short", "."],
            cwd=self.root,
            capture_output=True,
            encoding="utf-8",
        ).stdout.splitlines()
        # exclude untracked files
        status_lines = [line for line in status_lines if not line.startswith("?")]
        has_uncommitted_changes = len(status_lines) > 0
        if has_uncommitted_changes:
            logger.warning("There are uncommitted changes")
            print("Uncommitted changes:\n" + "\n".join(status_lines))
            print(
                "Preferably commit or stash them before running this script.\n"
                "Do you want to continue nonetheless? (y/n)"
            )
            answer = input()
            if answer.lower() != "y":
                logger.info("Aborting.")
                exit(1)

        self.replace_in_directory(self.root)
        self.replace_in_assets()
        subprocess.run(["git", "add", "-u", "."], cwd=self.root)

        subprocess.run(["git", "mv", "my_app", self.newname_underscore], cwd=self.root)
        subprocess.run(
            ["git", "mv", "my_app-assets", f"{self.newname_underscore}-assets"],
            cwd=self.root,
        )

        logger.info("Changes applied. Please review them before committing.")

    def should_skip(self, path: Path) -> bool:
        """Check if the given path is a directory or file that should be skipped."""
        if not (path.is_dir() or path.is_file()):
            return True

        for pattern in self.gitignore_patterns:
            relative_path = str(path.relative_to(self.root))
            if (
                fnmatch.fnmatch(relative_path, pattern)
                or fnmatch.fnmatch(path.name, pattern)
                or fnmatch.fnmatch(f"/{relative_path}", pattern)
            ):
                return True

        if path.is_dir():
            return path in self.skip_directories

        return path == THIS_FILE or path.suffix.lower() in IGNORE_EXTENSIONS


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(
        description="Rename my-app and my_app with a new name."
    )
    parser.add_argument(
        "newname", type=str, help="The new name to replace my-app and my_app with."
    )
    args = parser.parse_args()

    renamer = MyAppRenamer(args.newname)
    renamer.run()
