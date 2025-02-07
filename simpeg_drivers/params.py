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
import warnings
from copy import deepcopy
from pathlib import Path
from typing import ClassVar
from uuid import UUID

import numpy as np
from geoapps_utils.driver.data import BaseData
from geoapps_utils.driver.params import BaseParams
from geoh5py.data import BooleanData, FloatData, NumericData
from geoh5py.groups import SimPEGGroup, UIJsonGroup
from geoh5py.objects import DrapeModel, Octree, Points
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# from simpeg_drivers import assets_path


# pylint: disable=too-many-lines
# TODO: Remove this disable when all params are BaseData


class ActiveCellsData(BaseModel):
    """
    Active cells data as a topography surface or 3d model.

    :param topography_object: Topography object.
    :param topography: Topography data.
    :param active_model: Topography
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    topography_object: Points | None = None
    topography: FloatData | float | None = None
    active_model: BooleanData | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one(cls, data):
        if all(v is None for v in data.values()):
            raise ValueError("Must provide either topography or active model.")
        return data


class CoreData(BaseData):
    """
    Core parameters shared by inverse and forward operations.

    :param run_command: Command (module name) used to run the application from
        command line.
    :param conda_environment: Name of the conda environment used to run the
        application with all of its dependencies.
    :param inversion_type: Type of inversion.
    :param physical_property: Physical property of the model.
    :param data_object: Data object containing survey geometry and data
        channels.
    :param z_from_topo: If True, the z values of the data object are set to the
        topography surface.
    :param mesh: Mesh object containing models (starting, reference, active, etc..).
    :param starting_model: Starting model used to start inversion or for simulating
        data in the forward operation.
    :param active_cells: Active cell data as either a topography surface/data or a 3D model.
    :param tile_spatial: Number of tiles to split the data.
    :param parallelized: Parallelize the inversion/forward operation.
    :param n_cpu: Number of CPUs to use if parallelized.  If None, all cpu will be used.
    :param max_chunk_size: Maximum chunk size used for parallel operations.
    :param save_sensitivities: Save sensitivities to file.
    :param out_group: Output group to save results.
    :param generate_sweep: Generate sweep file instead of running the app.
    """

    # TODO: Refactor to allow frozen True.  Currently params.data_object is
    # updated after z_from_topo applied in entity_factory.py.  See
    # simpeg_drivers/components/data.py ln. 127
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True, extra="allow")
    run_command: ClassVar[str] = "simpeg_drivers.driver"
    conda_environment: str = "simpeg_drivers"
    inversion_type: str
    physical_property: str
    data_object: Points
    z_from_topo: bool = False
    mesh: Octree | None
    starting_model: float | FloatData
    active_cells: ActiveCellsData
    tile_spatial: int = 1
    parallelized: bool = True
    n_cpu: int | None = None
    max_chunk_size: int = 128
    save_sensitivities: bool = False
    out_group: SimPEGGroup | UIJsonGroup | None = None
    generate_sweep: bool = False

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
    def out_group_if_none(cls, data) -> SimPEGGroup:
        group = data.get("out_group", None)

        if isinstance(group, SimPEGGroup):
            return data

        if isinstance(group, UIJsonGroup | type(None)):
            name = cls.title if group is None else group.name
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

    @property
    def workpath(self):
        return Path(self.geoh5.h5file).parent

    @property
    def channels(self) -> list[str]:
        return [k.split("_")[0] for k in self.__dict__ if "channel" in k]

    def data_channel(self, component: str) -> NumericData | None:
        """Return the data object associated with the component."""
        return getattr(self, "_".join([component, "channel"]), None)

    def data(self, component: str) -> np.ndarray | None:
        """Returns array of data for chosen data component if it exists."""
        data_entity = self.data_channel(component)
        if isinstance(data_entity, NumericData):
            return data_entity.values.astype(float)
        return None

    def uncertainty_channel(self, component: str) -> NumericData | None:
        """Return the uncertainty object associated with the component."""
        return getattr(self, "_".join([component, "uncertainty"]), None)

    def uncertainty(self, component: str) -> np.ndarray | None:
        """Returns uncertainty for chosen data component if it exists."""

        uncertainty_entity = self.uncertainty_channel(component)
        if isinstance(uncertainty_entity, NumericData):
            return uncertainty_entity.values.astype(float)

        data = self.data(component)
        if data is not None:
            if isinstance(uncertainty_entity, int | float):
                return np.array([float(uncertainty_entity)] * len(data))
            else:
                return data * 0.0 + 1.0  # Default

        return None

    @property
    def padding_cells(self) -> int:
        """
        Default padding cells used for tiling.
        """
        # Keep whole mesh for 1 tile
        if self.tile_spatial == 1:
            return 100

        return 4 if self.inversion_type in ["fem", "tdem"] else 6


class BaseForwardData(CoreData):
    """
    Base class for forward parameters.

    See CoreData class docstring for addition parameters descriptions."""

    forward_only: bool = True

    @property
    def components(self) -> list[str]:
        """Retrieve component names used to index channel and uncertainty data."""
        comps = []
        for c in self.channels:
            if getattr(self, f"{c}_channel_bool", False):
                comps.append(c)

        return comps


class BaseInversionData(CoreData):
    """
    Base class for inversion parameters.

    See CoreData class docstring for addition parameters descriptions.

    :param reference_model: Reference model.
    :param lower_bound: Lower bound.
    :param upper_bound: Upper bound.

    :param alpha_s: Alpha s.
    :param length_scale_x: Length scale x.
    :param length_scale_y: Length scale y.
    :param length_scale_z: Length scale z.

    :param s_norm: S norm.
    :param x_norm: X norm.
    :param y_norm: Y norm.
    :param z_norm: Z norm.
    :param gradient_type: Gradient type.
    :param max_irls_iterations: Maximum IRLS iterations.
    :param starting_chi_factor: Starting chi factor.

    :param prctile: Prctile.
    :param beta_tol: Beta tolerance.

    :param chi_factor: Chi factor.
    :param auto_scale_misfits: Automatically scale misfits.
    :param initial_beta: Initial beta.
    :param initial_beta_ratio: Initial beta ratio.
    :param coolingFactor: Cooling factor.

    :param coolingRate: Cooling rate.
    :param max_global_iterations: Maximum global iterations.
    :param max_line_search_iterations: Maximum line search iterations.
    :param max_cg_iterations: Maximum CG iterations.
    :param tol_cg: Tolerance CG.
    :param f_min_change: F min change.

    :param sens_wts_threshold: Sensitivity weights threshold.
    :param every_iteration_bool: Every iteration bool.
    :param save_sensitivities: Save sensitivities.

    :param parallelized: Parallelized.
    :param n_cpu: Number of CPUs.
    :param tile_spatial: Tile the data spatially.
    :param store_sensitivities: Store sensitivities.
    :param max_chunk_size: Maximum chunk size.
    :param chunk_by_rows: Chunk by rows.

    :param out_group: Output group.

    :param generate_sweep: Generate sweep.

    :param output_tile_files: Output tile files.
    :param inversion_style: Inversion style.
    :param max_ram: Maximum RAM.    :param coolEps_q: Cool eps q.
    :param coolEpsFact: Cool eps fact.
    :param beta_search: Beta search.
    :param ga_group: GA group.
    :param distributed_workers: Distributed workers.
    :param no_data_value: No data value.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    name: ClassVar[str] = "Inversion"
    title: ClassVar[str] = "Geophysical inversion"
    run_command: ClassVar[str] = "simpeg_drivers.driver"

    forward_only: bool = False
    conda_environment: str = "simpeg_drivers"

    reference_model: float | FloatData | None = None
    lower_bound: float | FloatData | None = None
    upper_bound: float | FloatData | None = None

    alpha_s: float | FloatData = 1.0
    length_scale_x: float | FloatData = 1.0
    length_scale_y: float | FloatData = 1.0
    length_scale_z: float | FloatData = 1.0

    s_norm: float | FloatData = 0.0
    x_norm: float | FloatData = 2.0
    y_norm: float | FloatData = 2.0
    z_norm: float | FloatData = 2.0
    gradient_type: str = "total"
    max_irls_iterations: int = 25
    starting_chi_factor: float = 1.0

    chi_factor: float = 1.0
    auto_scale_misfits: bool = True
    initial_beta_ratio: float | None = 100.0
    initial_beta: float | None = None
    coolingFactor: float = 2.0

    coolingRate: float = 1.0
    max_global_iterations: int = 50
    max_line_search_iterations: int = 20
    max_cg_iterations: int = 30
    tol_cg: float = 1e-4
    f_min_change: float = 1e-2

    sens_wts_threshold: float = 1e-3
    every_iteration_bool: bool = True
    save_sensitivities: bool = False

    tile_spatial: int = 1
    store_sensitivities: str = "ram"

    beta_tol: float = 0.5
    prctile: float = 95.0
    coolEps_q: bool = True
    coolEpsFact: float = 1.2
    beta_search: bool = False

    chunk_by_rows: bool = True
    output_tile_files: bool = False
    inversion_style: str = "voxel"
    max_ram: float | None = None
    ga_group: SimPEGGroup | None = None
    distributed_workers: int | None = None
    no_data_value: float | None = None

    @property
    def components(self) -> list[str]:
        """Retrieve component names used to index channel and uncertainty data."""
        comps = []
        for c in self.channels:
            if getattr(self, f"{c}_channel", False):
                comps.append(c)

        return comps


class InversionBaseParams(BaseParams):
    """
    Base parameter class for geophysical->property inversion.
    """

    _default_ui_json = None
    _forward_defaults = None
    _inversion_defaults = None
    _inversion_type = None
    _physical_property = None

    def __init__(
        self,
        input_file: InputFile | None = None,
        forward_only: bool = False,
        **kwargs,
    ):
        self._forward_only: bool = (
            forward_only if input_file is None else input_file.data["forward_only"]
        )
        self._active_model: UUID = None
        self._auto_scale_misfits: bool = False  # Default to previous versions
        self._topography_object: UUID = None
        self._topography: UUID | float = None
        self._data_object: UUID = None
        self._starting_model: UUID | float = None
        self._tile_spatial = None
        self._z_from_topo: bool = None
        self._receivers_radar_drape = None
        self._receivers_offset_z: float = None
        self._gps_receivers_offset = None
        self._max_chunk_size: int = None
        self._chunk_by_rows: bool = None
        self._output_tile_files: bool = None
        self._mesh = None
        self._inversion_style: str = None
        self._chi_factor: float = None
        self._sens_wts_threshold: float = None
        self._every_iteration_bool: bool = None
        self._f_min_change: float = None
        self._beta_tol: float = None
        self._prctile: float = None
        self._coolingRate: float = None
        self._coolingFactor: float = None
        self._coolEps_q: bool = True
        self._coolEpsFact: float = 1.2
        self._beta_search: bool = False
        self._starting_chi_factor: float = 1.0
        self._max_irls_iterations: int = None
        self._max_global_iterations: int = None
        self._max_line_search_iterations: int = None
        self._max_cg_iterations: int = None
        self._initial_beta: float = None
        self._initial_beta_ratio: float = None
        self._tol_cg: float = None
        self._alpha_s: float = None
        self._length_scale_x: float = None
        self._length_scale_y: float = None
        self._length_scale_z: float = None
        self._s_norm: float = None
        self._x_norm: float = None
        self._y_norm: float = None
        self._z_norm: float = None
        self._reference_model = None
        self._gradient_type: str = None
        self._lower_bound = None
        self._upper_bound = None
        self._parallelized: bool = None
        self._n_cpu: int = None
        self._max_ram: float = None
        self._store_sensitivities: str = None
        self._save_sensitivities: bool = False
        self._out_group = None
        self._ga_group = None
        self._no_data_value: float = None
        self._distributed_workers = None
        self._documentation: str = ""
        self._generate_sweep: bool = False
        self._icon: str = ""
        self._defaults = (
            self._forward_defaults if self.forward_only else self._inversion_defaults
        )

        if input_file is None:
            ui_json = deepcopy(self._default_ui_json)
            ui_json = {
                k: ui_json[k] for k in list(self.defaults)
            }  # Re-order using defaults
            input_file = InputFile(
                ui_json=ui_json,
                data=self.defaults,
                validations=self.validations,
                validate=False,
            )

        super().__init__(input_file=input_file, **kwargs)

        if not self.forward_only:
            for key in self.__dict__:
                if "channel_bool" in key and getattr(self, key[:-5], None) is not None:
                    setattr(self, key, True)

    @property
    def active_cells(self):
        return ActiveCellsData(
            topography_object=self.topography_object,
            topography=self.topography,
            active_model=self.active_model,
        )

    def data_channel(self, component: str):
        """Return uuid of data channel."""
        return getattr(self, "_".join([component, "channel"]), None)

    @property
    def documentation(self):
        return self._documentation

    @documentation.setter
    def documentation(self, val):
        self.setter_validator("documentation", val)

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, val):
        self.setter_validator("icon", val)

    def uncertainty_channel(self, component: str):
        """Return uuid of uncertainty channel."""
        return getattr(self, "_".join([component, "uncertainty"]), None)

    def data(self, component: str):
        """Returns array of data for chosen data component."""
        data_entity = self.data_channel(component)
        if isinstance(data_entity, NumericData):
            return data_entity.values.astype(float)
        return None

    def uncertainty(self, component: str) -> np.ndarray | None:
        """Returns uncertainty for chosen data component."""
        val = self.uncertainty_channel(component)

        if isinstance(val, NumericData):
            return val.values.astype(float)
        elif self.data(component) is not None:
            d = self.data(component)
            if isinstance(val, int | float):
                return np.array([float(val)] * len(d))
            else:
                return d * 0.0 + 1.0  # Default
        else:
            return None

    @property
    def components(self) -> list[str]:
        """Retrieve component names used to index channel and uncertainty data."""
        comps = []
        channels = [
            k.lstrip("_").split("_channel_bool")[0]
            for k in self.__dict__
            if "channel_bool" in k
        ]

        for c in channels:
            if (
                getattr(self, f"{c}_channel", None) is not None
                or getattr(self, f"{c}_channel_bool", None) is True
            ):
                comps.append(c)

        return comps

    def model_norms(self) -> list[float]:
        """Returns model norm components as a list."""
        return [
            self.s_norm,
            self.x_norm,
            self.y_norm,
            self.z_norm,
        ]

    @property
    def forward_defaults(self):
        if getattr(self, "_forward_defaults", None) is None:
            raise NotImplementedError(
                "The property '_forward_defaults' must be assigned on "
                "the child inversion class."
            )
        return self._forward_defaults

    @property
    def forward_only(self):
        return self._forward_only

    @forward_only.setter
    def forward_only(self, val):
        self.setter_validator("forward_only", val)

    @property
    def inversion_defaults(self):
        if getattr(self, "_inversion_defaults", None) is None:
            raise NotImplementedError(
                "The property '_inversion_defaults' must be assigned on "
                "the child inversion class."
            )
        return self._inversion_defaults

    @property
    def active_model(self):
        return self._active_model

    @active_model.setter
    def active_model(self, val):
        self.setter_validator("active_model", val, fun=self._uuid_promoter)

    @property
    def auto_scale_misfits(self):
        return self._auto_scale_misfits

    @auto_scale_misfits.setter
    def auto_scale_misfits(self, val):
        self.setter_validator("auto_scale_misfits", val)

    @property
    def topography_object(self):
        return self._topography_object

    @topography_object.setter
    def topography_object(self, val):
        self.setter_validator("topography_object", val, fun=self._uuid_promoter)

    @property
    def topography(self):
        return self._topography

    @topography.setter
    def topography(self, val):
        self.setter_validator("topography", val, fun=self._uuid_promoter)

    @property
    def data_object(self):
        return self._data_object

    @data_object.setter
    def data_object(self, val):
        self.setter_validator("data_object", val, fun=self._uuid_promoter)

    @property
    def starting_model(self):
        return self._starting_model

    @starting_model.setter
    def starting_model(self, val):
        self.setter_validator("starting_model", val, fun=self._uuid_promoter)

    @property
    def tile_spatial(self):
        return self._tile_spatial

    @tile_spatial.setter
    def tile_spatial(self, val):
        self.setter_validator("tile_spatial", val, fun=self._uuid_promoter)

    @property
    def z_from_topo(self):
        return self._z_from_topo

    @z_from_topo.setter
    def z_from_topo(self, val):
        self.setter_validator("z_from_topo", val)

    @property
    def receivers_radar_drape(self):
        return self._receivers_radar_drape

    @receivers_radar_drape.setter
    def receivers_radar_drape(self, val):
        self.setter_validator("receivers_radar_drape", val, fun=self._uuid_promoter)
        warnings.warn(
            "The use of 'receivers_radar_drape' will be deprecated in future release.",
            DeprecationWarning,
        )

    @property
    def receivers_offset_z(self):
        return self._receivers_offset_z

    @receivers_offset_z.setter
    def receivers_offset_z(self, val):
        self.setter_validator("receivers_offset_z", val)
        warnings.warn(
            "The use of 'receiver_offset_z' will be deprecated in future release.",
            DeprecationWarning,
        )

    @property
    def generate_sweep(self):
        return self._generate_sweep

    @generate_sweep.setter
    def generate_sweep(self, val):
        self.setter_validator("generate_sweep", val)

    @property
    def gps_receivers_offset(self):
        return self._gps_receivers_offset

    @gps_receivers_offset.setter
    def gps_receivers_offset(self, val):
        self.setter_validator("gps_receivers_offset", val, fun=self._uuid_promoter)

    @property
    def inversion_type(self):
        return self._inversion_type

    @inversion_type.setter
    def inversion_type(self, val):
        self.setter_validator("inversion_type", val)

    @property
    def max_chunk_size(self):
        return self._max_chunk_size

    @max_chunk_size.setter
    def max_chunk_size(self, val):
        self.setter_validator("max_chunk_size", val)

    @property
    def chunk_by_rows(self):
        return self._chunk_by_rows

    @chunk_by_rows.setter
    def chunk_by_rows(self, val):
        self.setter_validator("chunk_by_rows", val)

    @property
    def output_tile_files(self):
        return self._output_tile_files

    @output_tile_files.setter
    def output_tile_files(self, val):
        self.setter_validator("output_tile_files", val)

    @property
    def mesh(self):
        return self._mesh

    @mesh.setter
    def mesh(self, val):
        self.setter_validator("mesh", val, fun=self._uuid_promoter)

        if (
            isinstance(self._mesh, Octree)
            and self._mesh.rotation is not None
            and self._mesh.rotation != 0.0
        ):
            raise ValueError(
                "Rotated meshes are not supported. Please use a mesh with an angle of 0.0."
            )

    @property
    def inversion_style(self):
        return self._inversion_style

    @inversion_style.setter
    def inversion_style(self, val):
        self.setter_validator("inversion_style", val)

    @property
    def chi_factor(self):
        return self._chi_factor

    @chi_factor.setter
    def chi_factor(self, val):
        self.setter_validator("chi_factor", val)

    @property
    def sens_wts_threshold(self):
        return self._sens_wts_threshold

    @sens_wts_threshold.setter
    def sens_wts_threshold(self, val):
        self.setter_validator("sens_wts_threshold", val)

    @property
    def every_iteration_bool(self):
        return self._every_iteration_bool

    @every_iteration_bool.setter
    def every_iteration_bool(self, val):
        self.setter_validator("every_iteration_bool", val)

    @property
    def f_min_change(self):
        return self._f_min_change

    @f_min_change.setter
    def f_min_change(self, val):
        self.setter_validator("f_min_change", val)

    @property
    def beta_tol(self):
        return self._beta_tol

    @beta_tol.setter
    def beta_tol(self, val):
        self.setter_validator("beta_tol", val)

    @property
    def prctile(self):
        return self._prctile

    @prctile.setter
    def prctile(self, val):
        self.setter_validator("prctile", val)

    @property
    def coolingRate(self):
        return self._coolingRate

    @coolingRate.setter
    def coolingRate(self, val):
        self.setter_validator("coolingRate", val)

    @property
    def coolingFactor(self):
        return self._coolingFactor

    @coolingFactor.setter
    def coolingFactor(self, val):
        self.setter_validator("coolingFactor", val)

    @property
    def coolEps_q(self):
        return self._coolEps_q

    @coolEps_q.setter
    def coolEps_q(self, val):
        self.setter_validator("coolEps_q", val)
        warnings.warn(
            "The use of 'coolEps_q' will be deprecated in future release.",
            DeprecationWarning,
        )

    @property
    def coolEpsFact(self):
        return self._coolEpsFact

    @coolEpsFact.setter
    def coolEpsFact(self, val):
        self.setter_validator("coolEpsFact", val)
        warnings.warn(
            "The use of 'coolEpsFact' will be deprecated in future release.",
            DeprecationWarning,
        )

    @property
    def beta_search(self):
        return self._beta_search

    @beta_search.setter
    def beta_search(self, val):
        self.setter_validator("beta_search", val)
        warnings.warn(
            "The use of 'beta_search' will be deprecated in future release.",
            DeprecationWarning,
        )

    @property
    def starting_chi_factor(self):
        return self._starting_chi_factor

    @starting_chi_factor.setter
    def starting_chi_factor(self, val):
        self.setter_validator("starting_chi_factor", val)

    @property
    def max_irls_iterations(self):
        return self._max_irls_iterations

    @max_irls_iterations.setter
    def max_irls_iterations(self, val):
        self.setter_validator("max_irls_iterations", val)

    @property
    def max_global_iterations(self):
        return self._max_global_iterations

    @max_global_iterations.setter
    def max_global_iterations(self, val):
        self.setter_validator("max_global_iterations", val)

    @property
    def max_line_search_iterations(self):
        return self._max_line_search_iterations

    @max_line_search_iterations.setter
    def max_line_search_iterations(self, val):
        self.setter_validator("max_line_search_iterations", val)

    @property
    def max_cg_iterations(self):
        return self._max_cg_iterations

    @max_cg_iterations.setter
    def max_cg_iterations(self, val):
        self.setter_validator("max_cg_iterations", val)

    @property
    def initial_beta(self):
        return self._initial_beta

    @initial_beta.setter
    def initial_beta(self, val):
        self.setter_validator("initial_beta", val)

    @property
    def initial_beta_ratio(self):
        return self._initial_beta_ratio

    @initial_beta_ratio.setter
    def initial_beta_ratio(self, val):
        self.setter_validator("initial_beta_ratio", val)

    @property
    def tol_cg(self):
        return self._tol_cg

    @tol_cg.setter
    def tol_cg(self, val):
        self.setter_validator("tol_cg", val)

    @property
    def alpha_s(self):
        return self._alpha_s

    @alpha_s.setter
    def alpha_s(self, val):
        self.setter_validator("alpha_s", val)

    @property
    def length_scale_x(self):
        return self._length_scale_x

    @length_scale_x.setter
    def length_scale_x(self, val):
        self.setter_validator("length_scale_x", val)

    @property
    def length_scale_y(self):
        return self._length_scale_y

    @length_scale_y.setter
    def length_scale_y(self, val):
        self.setter_validator("length_scale_y", val)

    @property
    def length_scale_z(self):
        return self._length_scale_z

    @length_scale_z.setter
    def length_scale_z(self, val):
        self.setter_validator("length_scale_z", val)

    @property
    def s_norm(self):
        return self._s_norm

    @s_norm.setter
    def s_norm(self, val):
        self.setter_validator("s_norm", val)

    @property
    def x_norm(self):
        return self._x_norm

    @x_norm.setter
    def x_norm(self, val):
        self.setter_validator("x_norm", val)

    @property
    def y_norm(self):
        return self._y_norm

    @y_norm.setter
    def y_norm(self, val):
        self.setter_validator("y_norm", val)

    @property
    def z_norm(self):
        return self._z_norm

    @z_norm.setter
    def z_norm(self, val):
        self.setter_validator("z_norm", val)

    @property
    def reference_model(self):
        return self._reference_model

    @reference_model.setter
    def reference_model(self, val):
        self.setter_validator("reference_model", val, fun=self._uuid_promoter)

    @property
    def gradient_type(self):
        return self._gradient_type

    @gradient_type.setter
    def gradient_type(self, val):
        self.setter_validator("gradient_type", val)

    @property
    def lower_bound(self):
        return self._lower_bound

    @lower_bound.setter
    def lower_bound(self, val):
        self.setter_validator("lower_bound", val, fun=self._uuid_promoter)

    @property
    def upper_bound(self):
        return self._upper_bound

    @upper_bound.setter
    def upper_bound(self, val):
        self.setter_validator("upper_bound", val, fun=self._uuid_promoter)

    @property
    def parallelized(self):
        return self._parallelized

    @parallelized.setter
    def parallelized(self, val):
        self.setter_validator("parallelized", val)

    @property
    def physical_property(self):
        """Physical property to invert."""
        return self._physical_property

    @property
    def n_cpu(self):
        if self._n_cpu is None:
            self._n_cpu = multiprocessing.cpu_count()
        return self._n_cpu

    @n_cpu.setter
    def n_cpu(self, val):
        self.setter_validator("n_cpu", val)

    @property
    def max_ram(self):
        return self._max_ram

    @max_ram.setter
    def max_ram(self, val):
        self.setter_validator("max_ram", val)

    @property
    def store_sensitivities(self):
        return self._store_sensitivities

    @store_sensitivities.setter
    def store_sensitivities(self, val):
        self.setter_validator("store_sensitivities", val)

    @property
    def save_sensitivities(self):
        return self._save_sensitivities

    @save_sensitivities.setter
    def save_sensitivities(self, val):
        self.setter_validator("save_sensitivities", val)

    @property
    def out_group(self) -> SimPEGGroup | None:
        """Return the SimPEGGroup object."""
        return self._out_group

    @out_group.setter
    def out_group(self, val):
        self.setter_validator("out_group", val)

    @property
    def ga_group(self) -> str:
        """GA group name."""
        return self._ga_group

    @ga_group.setter
    def ga_group(self, val):
        self.setter_validator("ga_group", val)

    @property
    def distributed_workers(self):
        return self._distributed_workers

    @distributed_workers.setter
    def distributed_workers(self, val):
        self.setter_validator("distributed_workers", val)

    @property
    def unit_conversion(self):
        """Return unit conversion factor."""
        return None

    def update_group_options(self):
        """
        Add options to the SimPEGGroup inversion using input file class.
        """
        if self._input_file is not None and self._out_group is not None:
            with fetch_active_workspace(self.geoh5, mode="r+"):
                ui_json = self.to_dict(ui_json_format=True)
                self._out_group.options = ui_json
                self._out_group.metadata = None

    @property
    def padding_cells(self) -> int:
        """
        Default padding cells used for tiling.
        """
        # Keep whole mesh for 1 tile
        if self.tile_spatial == 1:
            return 100

        return 4 if self.inversion_type in ["fem", "tdem"] else 8
