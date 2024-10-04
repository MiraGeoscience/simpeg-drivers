# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#  All rights reserved.
#
#  This file is part of simpeg-drivers.
#
#  The software and information contained herein are proprietary to, and
#  comprise valuable trade secrets of, Mira Geoscience, which
#  intend to preserve as trade secrets such software and information.
#  This software is furnished pursuant to a written license agreement and
#  may be used, copied, transmitted, and stored only in accordance with
#  the terms of such license and with the inclusion of the above copyright
#  notice.  This software and information or any other copies thereof may
#  not be provided or otherwise made available to any other person.
#
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from geoh5py.data import FilenameData
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import DrapeModel, PotentialElectrode
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace
from param_sweeps.driver import SweepDriver, SweepParams
from param_sweeps.generate import generate

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.utils.utils import active_from_xyz, drape_to_octree


class LineSweepDriver(SweepDriver, InversionDriver):
    def __init__(self, params):
        self._out_group = None
        self.workspace = params.geoh5
        self.pseudo3d_params = params
        self.cleanup = params.cleanup

        if (
            hasattr(self.pseudo3d_params, "out_group")
            and self.pseudo3d_params.out_group is None
        ):
            self.pseudo3d_params.out_group = self.out_group

        super().__init__(self.setup_params())

    @property
    def out_group(self):
        """The SimPEGGroup"""
        if self._out_group is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                name = self.pseudo3d_params.inversion_type.capitalize()
                if self.pseudo3d_params.forward_only:
                    name += "Forward"
                else:
                    name += "Inversion"

                # with fetch_active_workspace(self.geoh5, mode="r+"):
                self._out_group = SimPEGGroup.create(
                    self.pseudo3d_params.geoh5, name=name
                )
                self.pseudo3d_params.out_group = self._out_group
                self.pseudo3d_params.update_group_options()

        return self._out_group

    def run(self):  # pylint: disable=W0221
        super().run()  # pylint: disable=W0221
        with self.workspace.open(mode="r+"):
            self.collect_results()
        if self.cleanup:
            self.file_cleanup()

    def setup_params(self):
        h5_file_path = Path(self.workspace.h5file).resolve()
        ui_json_path = h5_file_path.parent / (
            re.sub(r"\.ui$", "", h5_file_path.stem) + ".ui.json"
        )
        if not (ui_json_path).is_file():
            with self.workspace.open():
                self.pseudo3d_params.write_input_file(
                    name=ui_json_path.name,
                    path=h5_file_path.parent,
                )
        generate(
            ui_json_path,
            parameters=["line_id"],
            update_values={"conda_environment": "simpeg_drivers"},
        )
        ifile = InputFile.read_ui_json(
            h5_file_path.parent
            / (re.sub(r"\.ui$", "", h5_file_path.stem) + "_sweep.ui.json")
        )
        with self.workspace.open(mode="r"):
            lines = self.pseudo3d_params.line_object.values
        ifile.data["line_id_start"] = int(lines.min())
        ifile.data["line_id_end"] = int(lines.max())
        ifile.data["line_id_n"] = len(np.unique(lines))
        sweep_params = SweepParams.from_input_file(ifile)
        sweep_params.geoh5 = self.workspace
        return sweep_params

    def file_cleanup(self):
        """Remove files associated with the parameter sweep."""
        path = Path(self.workspace.h5file).parent
        with open(path / "lookup.json", encoding="utf8") as f:
            files = list(json.load(f))

        files = [f"{f}.ui.json" for f in files] + [f"{f}.ui.geoh5" for f in files]
        files += ["lookup.json"]
        files += [f.name for f in path.glob("*_sweep.ui.json")]

        for file in files:
            (path / file).unlink(missing_ok=True)

    @staticmethod
    def line_files(path: str | Path):
        with open(Path(path) / "lookup.json", encoding="utf8") as file:
            line_files = {v["line_id"]: k for k, v in json.load(file).items()}
        return line_files

    def collect_results(self):
        path = Path(self.workspace.h5file).parent
        files = LineSweepDriver.line_files(str(path))
        line_ids = self.pseudo3d_params.line_object.values
        data = {}
        drape_models = []

        out_lines = []
        log_lines = []
        for line in np.unique(line_ids):
            with Workspace(f"{path / files[line]}.ui.geoh5") as ws:
                out_group = next(
                    group for group in ws.groups if isinstance(group, SimPEGGroup)
                )
                survey = next(
                    child
                    for child in out_group.children
                    if isinstance(child, PotentialElectrode)
                )
                line_data = survey.get_entity(self.pseudo3d_params.line_object.name)

                if not line_data:
                    raise ValueError(f"Line {line} not found in {survey.name}")

                line_indices = line_ids == line
                data = self.collect_line_data(survey, line_indices, data)
                mesh = next(
                    child
                    for child in out_group.children
                    if isinstance(child, DrapeModel)
                )

                local_simpeg_group = mesh.parent.copy(
                    name=f"Line {line}",
                    parent=self.pseudo3d_params.out_group,
                    copy_children=False,
                )
                local_simpeg_group.options = mesh.parent.options
                filedata = [
                    k for k in out_group.children if isinstance(k, FilenameData)
                ]
                for fdat in filedata:
                    if ".out" in fdat.name:
                        out_lines += [f"Line {line} from file {files[line]}\n"]
                        out_lines += fdat.file_bytes.decode(encoding="utf8").split(
                            sep="\n"
                        )
                        out_lines += ["\n"]

                    if ".log" in fdat.name:
                        log_lines += fdat.file_bytes.decode(encoding="utf8").split(
                            sep="\n"
                        )
                        log_lines += ["\n"]

                    fdat.copy(parent=out_group)

                sub_mesh = mesh.copy(parent=local_simpeg_group)
                drape_models.append(sub_mesh)

        # Write new log files to disk
        with open(ws.h5file.parent / "SimPEG.out", "w", encoding="utf8") as f:
            f.write("".join(out_lines))

        with open(ws.h5file.parent / "SimPEG.log", "w", encoding="utf8") as f:
            f.write("".join(log_lines))

        self.pseudo3d_params.data_object.add_data(data)

        if self.pseudo3d_params.mesh is None:
            return

        # interpolate drape model children common to all drape models into octree
        active = active_from_xyz(
            self.pseudo3d_params.mesh, self.inversion_topography.locations
        )
        common_children = set.intersection(
            *[{c.name for c in d.children} for d in drape_models]
        )
        children = {n: [n] * len(drape_models) for n in common_children}
        octree_model = drape_to_octree(
            self.pseudo3d_params.mesh, drape_models, children, active, method="nearest"
        )

        # interpolate last iterations for each drape model into octree
        iter_children = [
            [c.name for c in m.children if "iteration" in c.name.lower()]
            for m in drape_models
        ]
        if any(iter_children):
            iter_numbers = [
                [int(re.findall(r"\d+", n)[0]) for n in k] for k in iter_children
            ]
            last_iterations = [np.where(k == np.max(k))[0][0] for k in iter_numbers]
            label = iter_children[0][0].replace(
                re.findall(r"\d+", iter_children[0][0])[0], "final"
            )
            children = {
                label: [c[last_iterations[i]] for i, c in enumerate(iter_children)]
            }
            octree_model = drape_to_octree(
                self.pseudo3d_params.mesh,
                drape_models,
                children,
                active,
                method="nearest",
            )

        octree_model.copy(parent=self.pseudo3d_params.out_group)

    def collect_line_data(self, survey, line_indices, data):
        """
        Fill chunks of values from one line
        """
        for child in survey.children:  # initialize data values dictionary
            if "Iteration" in child.name and child.name not in data:
                data[child.name] = {"values": np.zeros_like(line_indices) * np.nan}

        for child in survey.children:
            if "Iteration" in child.name:
                data[child.name]["values"][line_indices] = child.values

        return data
