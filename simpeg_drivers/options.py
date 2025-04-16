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

from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import ClassVar, TypeAlias

import numpy as np
from geoapps_utils.driver.data import BaseData
from geoh5py.data import (
    BooleanData,
    DataAssociationEnum,
    FloatData,
    IntegerData,
    NumericData,
    ReferencedData,
)
from geoh5py.groups import PropertyGroup, SimPEGGroup, UIJsonGroup
from geoh5py.objects import DrapeModel, Octree, Points
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

import simpeg_drivers


logger = getLogger(__name__)

InversionDataDict: TypeAlias = (
    dict[str, np.ndarray | None] | dict[str, dict[float, np.ndarray | None]]
)


class ActiveCellsOptions(BaseModel):
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
    active_model: BooleanData | IntegerData | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one(cls, data):
        if all(v is None for v in data.values()):
            raise ValueError("Must provide either topography or active model.")
        return data


class SolverType(str, Enum):
    """
    Supported solvers.
    """

    Pardiso = "Pardiso"
    Mumps = "Mumps"


class CoreOptions(BaseData):
    """
    Core parameters shared by inverse and forward operations.

    :param run_command: Command (module name) used to run the application from
        command line.
    :param conda_environment: Name of the conda environment used to run the
        application with all of its dependencies.
    :param inversion_type: Type of inversion.
    :param data_object: Data object containing survey geometry and data
        channels.
    :param mesh: Mesh object containing models (starting, reference, active, etc..).
    :param starting_model: Starting model used to start inversion or for simulating
        data in the forward operation.
    :param active_cells: Active cell data as either a topography surface/data or a 3D model.
    :param tile_spatial: Number of tiles to split the data.
    :param max_chunk_size: Maximum chunk size used for parallel operations.
    :param save_sensitivities: Save sensitivities to file.
    :param out_group: Output group to save results.
    :param generate_sweep: Generate sweep file instead of running the app.
    :param distributed_workers: Distributed workers.
    """

    # TODO: Refactor to allow frozen True.  Currently params.data_object is
    # updated after z_from_topo applied in entity_factory.py.  See
    # simpeg_drivers/components/data.py ln. 127
    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,
        extra="allow",
        validate_default=True,
    )

    title: str | None = None
    icon: str | None = None
    documentation: str | None = None
    version: str = simpeg_drivers.__version__
    run_command: str = "simpeg_drivers.driver"
    conda_environment: str = "simpeg_drivers"
    inversion_type: str
    data_object: Points
    mesh: Octree | DrapeModel | None
    starting_model: float | FloatData
    active_cells: ActiveCellsOptions
    tile_spatial: int = 1
    n_cpu: int | None = None
    solver_type: SolverType = SolverType.Pardiso
    save_sensitivities: bool = False
    max_chunk_size: int = 128
    out_group: SimPEGGroup | UIJsonGroup | None = None
    generate_sweep: bool = False
    distributed_workers: str | None = None

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

    @property
    def workpath(self):
        return Path(self.geoh5.h5file).parent

    @property
    def components(self) -> list[str]:
        """Return list of component names."""
        return [self._component_name(k) for k in self.__dict__ if "channel" in k]

    @property
    def active_components(self) -> list[str]:
        """Return list of active components."""
        return [
            k
            for k in self.components
            if getattr(self, "_".join([k, "channel"])) is not None
        ]

    @property
    def data(self) -> InversionDataDict:
        """Return dictionary of data components and associated values."""
        out = {}
        for k in self.active_components:
            out[k] = self.component_data(k)
        return out

    @property
    def uncertainties(self) -> InversionDataDict:
        """Return dictionary of unceratinty components and associated values."""
        out = {}
        for k in self.active_components:
            out[k] = self.component_uncertainty(k)
        return out

    def component_data(self, component: str) -> np.ndarray | None:
        """Return data values associated with the component."""
        data = getattr(self, "_".join([component, "channel"]), None)
        if isinstance(data, NumericData):
            data = data.values
        return data

    def component_uncertainty(self, component: str) -> np.ndarray | None:
        """
        Return uncertainty values associated with the component.

        If the uncertainty is a float, it will be broadcasted to the same
        shape as the data.

        :param component: Component name.
        """
        data = getattr(self, "_".join([component, "uncertainty"]), None)
        if isinstance(data, NumericData):
            data = data.values
        elif isinstance(data, float):
            data *= np.ones_like(self.component_data(component))

        return data

    def _component_name(self, component: str) -> str:
        """Strip the '_channel' and '_channel_bool' suffixes from data name."""
        return "_".join(
            [k for k in component.split("_") if k not in ["channel", "bool"]]
        )

    @property
    def padding_cells(self) -> int:
        """
        Default padding cells used for tiling.
        """
        # Keep whole mesh for 1 tile
        if self.tile_spatial == 1:
            return 100

        return 4 if self.inversion_type in ["fdem", "tdem"] else 6

    def _create_input_file_from_attributes(self) -> InputFile:
        ifile = super()._create_input_file_from_attributes()
        ifile.set_data_value("version", simpeg_drivers.__version__)
        return ifile


class BaseForwardOptions(CoreOptions):
    """
    Base class for forward parameters.

    See CoreData class docstring for addition parameters descriptions."""

    forward_only: bool = True

    @property
    def active_components(self) -> list[str]:
        """Return list of active components."""
        return [k for k in self.components if getattr(self, f"{k}_channel_bool")]


class BaseInversionOptions(CoreOptions):
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
    :param gradient_rotation: Property group for gradient rotation angles.

    :param s_norm: S norm.
    :param x_norm: X norm.
    :param y_norm: Y norm.
    :param z_norm: Z norm.
    :param gradient_type: Gradient type.
    :param max_irls_iterations: Maximum IRLS iterations.
    :param starting_chi_factor: Starting chi factor.

    :param percentile: Percentile.
    :param beta_tol: Beta tolerance.

    :param chi_factor: Chi factor.
    :param auto_scale_misfits: Automatically scale misfits.
    :param initial_beta: Initial beta.
    :param initial_beta_ratio: Initial beta ratio.
    :param cooling_factor: Cooling factor.

    :param cooling_rate: Cooling rate.
    :param max_global_iterations: Maximum global iterations.
    :param max_line_search_iterations: Maximum line search iterations.
    :param max_cg_iterations: Maximum CG iterations.
    :param tol_cg: Tolerance CG.
    :param f_min_change: F min change.

    :param sens_wts_threshold: Sensitivity weights threshold.
    :param every_iteration_bool: Every iteration bool.

    :param solver_type: Direct solver provider.  Either Mumps or Pardiso.
    :param tile_spatial: Tile the data spatially.
    :param store_sensitivities: Store sensitivities.
    :param max_chunk_size: Maximum chunk size.
    :param chunk_by_rows: Chunk by rows.

    :param out_group: Output group.

    :param generate_sweep: Generate sweep.

    :param coolEpsFact: Cool eps fact.
    :param beta_search: Beta search.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    name: ClassVar[str] = "Inversion"

    title: str = "Geophysical inversion"
    run_command: str = "simpeg_drivers.driver"

    forward_only: bool = False
    conda_environment: str = "simpeg_drivers"

    reference_model: float | FloatData | None = None
    lower_bound: float | FloatData | None = None
    upper_bound: float | FloatData | None = None

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
    def gradient_dip(self) -> np.ndarray | None:
        """Gradient dip angle in clockwise radians from horizontal."""
        if self.gradient_rotation is not None:
            dip_uid = self.gradient_rotation.properties[1]
            dips = self.geoh5.get_entity(dip_uid)[0].values
            return np.deg2rad(dips)
        return None

    @property
    def gradient_direction(self) -> np.ndarray | None:
        """Gradient direction angle in clockwise radians from north"""
        if self.gradient_rotation is not None:
            from geoh5py.groups.property_group_type import GroupTypeEnum

            direction_uid = self.gradient_rotation.properties[0]
            directions = self.geoh5.get_entity(direction_uid)[0].values
            if self.gradient_rotation.property_group_type == GroupTypeEnum.STRIKEDIP:
                directions += 90.0
            return np.deg2rad(directions)
        return None


class EMDataMixin:
    """
    Mixin class to add data and uncertainty access from property groups.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def component_data(self, component: str):
        """Return data values associated with the component."""
        property_group = getattr(self, "_".join([component, "channel"]), None)
        return self.property_group_data(property_group)

    def component_uncertainty(self, component: str):
        """Return uncertainty values associated with the component."""
        property_group = getattr(self, "_".join([component, "uncertainty"]), None)
        return self.property_group_data(property_group)

    def property_group_data(self, property_group: PropertyGroup):
        """
        Return dictionary of channel/data.

        :param property_group: Property group uid
        """
        frequencies = self.data_object.channels
        if property_group is None:
            return {f: None for f in frequencies}

        data = {}
        group = next(
            k for k in self.data_object.property_groups if k.uid == property_group.uid
        )
        property_names = [self.geoh5.get_entity(p)[0].name for p in group.properties]
        properties = [self.geoh5.get_entity(p)[0].values for p in group.properties]
        for i, f in enumerate(frequencies):
            try:
                f_ind = property_names.index(
                    next(k for k in property_names if f"{f:.2e}" in k)
                )  # Safer if data was saved with geoapps naming convention
                data[f] = properties[f_ind]
            except StopIteration:
                data[f] = properties[i]  # in case of other naming conventions

        return data


class DrapeModelOptions(BaseModel):
    """
    Drape model parameters for 2D simulation/inversion].

    :param u_cell_size: Horizontal cell size for the drape model.
    :param v_cell_size: Vertical cell size for the drape model.
    :param depth_core: Depth of the core region.
    :param horizontal_padding: Horizontal padding.
    :param vertical_padding: Vertical padding.
    :param expansion_factor: Expansion factor for the drape model.
    """

    u_cell_size: float | None = 25.0
    v_cell_size: float | None = 25.0
    depth_core: float | None = 100.0
    horizontal_padding: float | None = 100.0
    vertical_padding: float | None = 100.0
    expansion_factor: float | None = 1.1


class LineSelectionOptions(BaseModel):
    """
    Line selection parameters for 2D inversions.

    :param line_object: Reference data categorizing survey by line ids.
    :param line_id: Line identifier for simulation/inversion.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    line_object: ReferencedData
    line_id: int = 1

    @field_validator("line_object", mode="before")
    @classmethod
    def validate_cell_association(cls, value):
        if value.association is not DataAssociationEnum.CELL:
            raise ValueError("Line identifier must be associated with cells.")
        return value

    @model_validator(mode="after")
    def line_id_referenced(self):
        if self.line_id not in self.line_object.values:
            raise ValueError("Line id isn't referenced in the line object.")
        return self
