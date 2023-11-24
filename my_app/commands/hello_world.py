#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of my_app package.
#
#  All rights reserved.

from __future__ import annotations

import sys
import tkinter as tk

from geoh5py.ui_json import InputFile


def hello(name: str) -> None:
    """
    Pops up a greeting dialog box with the given message.
    """

    root = tk.Tk()
    root.title(name)
    root.geometry("300x200")
    root.resizable(False, False)

    label = tk.Label(root, text=f"Hello, {name} !")
    label.pack()

    root.mainloop()


if __name__ == "__main__":
    assert len(sys.argv) > 1, "No input file provided"

    ifile = InputFile.read_ui_json(sys.argv[1])
    params = ifile.data
    hello(params["name"])
