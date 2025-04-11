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

import multiprocessing

from geoapps_utils.driver.data import BaseData
from geoh5py.data import FloatData
from geoh5py.groups import PropertyGroup, SimPEGGroup, UIJsonGroup
from geoh5py.objects import DrapeModel, Octree
from geoh5py.shared.utils import fetch_active_workspace
from pydantic import ConfigDict, field_validator, model_validator

import simpeg_drivers
from simpeg_drivers.options import ActiveCellsOptions, SolverType


class BaseJointOptions(BaseData):
    """
    Base Joint Options.

    :param group_a: First SimPEGGroup with options set for inversion.
    :param group_a_multiplier: Multiplier for the data misfit function for Group A.
    :param group_b: Second SimPEGGroup with options set for inversion.
    :param group_b_multiplier: Multiplier for the data misfit function for Group B.
    :param group_c: Third SimPEGGroup with options set for inversion.
    :param group_c_multiplier: Multiplier for the data misfit function for Group C.
    """

    model_config = ConfigDict(frozen=False)

    icon: str | None = None
    documentation: str | None = None
    version: str = simpeg_drivers.__version__
    run_command: str = "simpeg_drivers.driver"
    conda_environment: str = "simpeg-drivers"
    forward_only: bool = False
    physical_property: list[str] = ["conductivity"]

    group_a: SimPEGGroup
    group_a_multiplier: float = 1.0
    group_b: SimPEGGroup
    group_b_multiplier: float = 1.0
    group_c: SimPEGGroup | None = None
    group_c_multiplier: float | None = None

    mesh: Octree | DrapeModel | None

    active_cells: ActiveCellsOptions
    tile_spatial: int = 1
    parallelized: bool = True
    solver_type: SolverType = SolverType.Pardiso
    save_sensitivities: bool = False
    n_cpu: int | None = None
    max_chunk_size: int = 128
    out_group: SimPEGGroup | UIJsonGroup | None = None
    generate_sweep: bool = False
    distributed_workers: str | None = None
    alpha_s: float | FloatData | None = 1.0
    length_scale_x: float | FloatData = 1.0
    length_scale_y: float | FloatData | None = 1.0
    length_scale_z: float | FloatData = 1.0
    gradient_rotation: PropertyGroup | None = None
    s_norm: float | FloatData | None = 0.0
    x_norm: float | FloatData = 2.0
    y_norm: float | FloatData | None = 2.0
    z_norm: float | FloatData = 2.0
    gradient_type: str = "total"
    max_irls_iterations: int = 25
    starting_chi_factor: float = 1.0

    chi_factor: float = 1.0
    auto_scale_misfits: bool = True
    initial_beta_ratio: float | None = 100.0
    initial_beta: float | None = None
    cooling_factor: float = 2.0

    cooling_rate: float = 1.0
    max_global_iterations: int = 50
    max_line_search_iterations: int = 20
    max_cg_iterations: int = 30
    tol_cg: float = 1e-4
    f_min_change: float = 1e-2
    solver_type: SolverType = SolverType.Pardiso

    sens_wts_threshold: float = 1e-3
    every_iteration_bool: bool = True

    store_sensitivities: str = "ram"

    beta_tol: float = 0.5
    percentile: float = 95.0
    epsilon_cooling_factor: float = 1.2

    @property
    def groups(self) -> list[SimPEGGroup]:
        """List all active groups."""
        return [k for k in [self.group_a, self.group_b, self.group_c] if k is not None]

    @field_validator("n_cpu", mode="before")
    @classmethod
    def maximize_cpu_if_none(cls, value):
        if value is None:
            value = int(multiprocessing.cpu_count())
        return value

    @field_validator("mesh", mode="before")
    @classmethod
    def mesh_cannot_be_rotated(cls, value: Octree):
        if isinstance(value, Octree) and value.rotation not in [0.0, None]:
            raise ValueError(
                "Rotated meshes are not supported. Please use a mesh with an angle of 0.0."
            )
        return value

    @model_validator(mode="before")
    @classmethod
    def out_group_if_none(cls, data):
        group = data.get("out_group", None)

        if isinstance(group, SimPEGGroup):
            return data

        if isinstance(group, UIJsonGroup | type(None)):
            name = (
                cls.model_fields["title"].default  # pylint: disable=unsubscriptable-object
                if group is None
                else group.name
            )
            with fetch_active_workspace(data["geoh5"], mode="r+") as geoh5:
                group = SimPEGGroup.create(geoh5, name=name)

        data["out_group"] = group

        return data

    @model_validator(mode="after")
    def update_out_group_options(self):
        assert self.out_group is not None
        with fetch_active_workspace(self.geoh5, mode="r+"):
            self.out_group.options = self.serialize()
            self.out_group.metadata = None
        return self
