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

import json
import re
from pathlib import Path

import numpy as np
from geoapps_utils.param_sweeps.driver import SweepDriver, SweepParams
from geoapps_utils.param_sweeps.generate import generate
from geoapps_utils.run import load_ui_json_as_dict
from geoapps_utils.utils.importing import GeoAppsError
from geoh5py.data import FilenameData
from geoh5py.groups import ContainerGroup, SimPEGGroup
from geoh5py.objects import DrapeModel, PotentialElectrode, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace

from simpeg_drivers.driver import InversionDriver
from simpeg_drivers.options import BaseInversionOptions
from simpeg_drivers.utils.utils import active_from_xyz, drape_to_octree


class LineSweepDriver(SweepDriver, InversionDriver):
    """Line Sweep driver for batch 2D forward and inversion drivers."""

    _params_class = SweepParams

    def __init__(self, params):
        self.batch2d_params = params
        self.cleanup = params.file_control.cleanup

        params = self.setup_params()
        params.inversion_type = self.batch2d_params.inversion_type
        super().__init__(params)

    @property
    def out_group(self):
        """The SimPEGGroup"""
        return self._out_group

    @out_group.setter
    def out_group(self, value: SimPEGGroup):
        if not isinstance(value, SimPEGGroup):
            raise TypeError("Output group must be a SimPEGGroup.")

        self.batch2d_params.out_group = value
        self.batch2d_params.update_out_group_options()
        self._out_group = value

    def validate_out_group(self, out_group: SimPEGGroup | None) -> SimPEGGroup:
        """
        Validate or create a SimPEGGroup to store results.

        :param out_group: Output group from selection.
        """
        if isinstance(out_group, SimPEGGroup):
            return out_group

        with fetch_active_workspace(self.workspace, mode="r+"):
            out_group = SimPEGGroup.create(
                self.workspace, name=self.batch2d_params.title
            )

        return out_group

    def run(self):
        """
        Run the line sweep driver.

        TODO: Add parallelization on GEOPY-2490
        """
        with fetch_active_workspace(self.workspace, mode="r+"):
            if not isinstance(self.out_group, SimPEGGroup):
                raise GeoAppsError(
                    f"Output group should be a valid SimPEGGroup, received: {type(self.out_group)}."
                )

            lookup = self.get_lookup()
            self.write_files(lookup)

            for name, trial in lookup.items():
                file_path = Path(self.working_directory) / f"{name}.ui.json"
                if trial["status"] == "complete":
                    continue

                trial["status"] = "processing"
                self.update_lookup(lookup)
                params_dict = load_ui_json_as_dict(file_path)
                driver = self.driver_class_from_name(
                    params_dict["inversion_type"],
                    forward_only=params_dict["forward_only"],
                )
                driver.start(file_path)

                trial["status"] = "complete"
                self.update_lookup(lookup)

            self.collect_results()

        if self.cleanup:
            self.file_cleanup()

    def setup_params(self):
        h5_file_path = Path(self.workspace.h5file).resolve()
        ui_json_path = h5_file_path.parent / (
            re.sub(r"\.ui$", "", h5_file_path.stem) + ".ui.json"
        )
        if not (ui_json_path).is_file():
            with fetch_active_workspace(self.workspace):
                self.batch2d_params.write_ui_json(
                    path=h5_file_path.parent / ui_json_path.name
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
        with fetch_active_workspace(self.workspace):
            lines = self.batch2d_params.line_selection.line_object.values
        ifile.data["line_id_start"] = int(lines.min())
        ifile.data["line_id_end"] = int(lines.max())
        ifile.data["line_id_n"] = len(np.unique(lines))
        sweep_params = SweepParams.build(ifile)
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
        line_ids = self.batch2d_params.line_selection.line_object.values
        data = {}
        drape_models = []

        out_lines = []
        log_lines = []
        for line in np.unique(line_ids):
            with Workspace(f"{path / files[line]}.ui.geoh5") as ws:
                out_group = next(
                    group for group in ws.groups if isinstance(group, SimPEGGroup)
                )
                run_group = ContainerGroup.create(
                    self.workspace, name=f"Line {line}", parent=self.out_group
                )
                local_simpeg_group = out_group.copy(
                    parent=run_group, copy_children=True, copy_relatives=True
                )
                survey = next(
                    child
                    for child in local_simpeg_group.children
                    if isinstance(child, PotentialElectrode)
                )
                line_data = survey.get_entity(
                    self.batch2d_params.line_selection.line_object.name
                )

                if not line_data:
                    raise GeoAppsError(f"Line {line} not found in {survey.name}")

                line_indices = line_ids == line
                data = self.collect_line_data(survey, line_indices, data)
                mesh = next(
                    child
                    for child in local_simpeg_group.children
                    if isinstance(child, DrapeModel)
                )
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

                drape_models.append(mesh)

        # Write new log files to disk
        with open(ws.h5file.parent / "SimPEG.out", "w", encoding="utf8") as f:
            f.write("".join(out_lines))

        with open(ws.h5file.parent / "SimPEG.log", "w", encoding="utf8") as f:
            f.write("".join(log_lines))

        self.batch2d_params.data_object.add_data(data)

        if self.batch2d_params.mesh is None:
            return

        # interpolate drape model children common to all drape models into octree
        active = active_from_xyz(
            self.batch2d_params.mesh, self.inversion_topography.locations
        )
        common_children = set.intersection(
            *[{c.name for c in d.children} for d in drape_models]
        )
        children = {n: [n] * len(drape_models) for n in common_children}
        octree_model = drape_to_octree(
            self.batch2d_params.mesh, drape_models, children, active, method="nearest"
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
            label = re.sub(r"\d+", "final", iter_children[0][0])
            children = {
                label: [c[last_iterations[i]] for i, c in enumerate(iter_children)]
            }
            octree_model = drape_to_octree(
                self.batch2d_params.mesh,
                drape_models,
                children,
                active,
                method="nearest",
            )

        octree_model.copy(parent=self.out_group)

    def collect_line_data(self, survey, line_indices, data):
        """
        Fill chunks of values from one line
        """
        for name in survey.get_data_list():
            if "Iteration" not in name:
                continue

            child = survey.get_entity(name)[0]
            if name not in data:
                data[name] = {"values": np.zeros_like(line_indices) * np.nan}

            data[name]["values"][line_indices] = child.values

            if isinstance(self.batch2d_params, BaseInversionOptions):
                label = re.sub(r"\d+", "final", name)

                if label not in data:
                    data[label] = {"values": np.zeros_like(line_indices) * np.nan}

                data[label]["values"][line_indices] = child.values

        return data

    @property
    def workspace(self):
        """Application workspace."""
        return self.batch2d_params.geoh5
