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

from logging import getLogger
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, TypeAlias

import numpy as np
from geoapps_utils.base import Options
from geoh5py.data import (
    BooleanData,
    DataAssociationEnum,
    FloatData,
    IntegerData,
    NumericData,
    ReferencedData,
)
from geoh5py.groups import PropertyGroup, SimPEGGroup, UIJsonGroup
from geoh5py.objects import DrapeModel, Grid2D, Octree, Points
from geoh5py.objects.surveys.electromagnetics.base import BaseEMSurvey
from geoh5py.ui_json import InputFile
from geoh5py.ui_json.utils import fetch_active_workspace
from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from . import public_version
from .utils.regularization import direction_and_dip


logger = getLogger(__name__)

InversionDataDict: TypeAlias = (
    dict[str, np.ndarray | None] | dict[str, dict[float, np.ndarray | None]]
)


def deprecate_warning(value, info):
    """Issue deprecation warning."""
    logger.warning(
        "Deprecated field '%s' will be ignored. Results may be affected.",
        info.field_name,
    )
    return value


Deprecated = Annotated[
    Any,
    Field(default=None),
    BeforeValidator(deprecate_warning),
]


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
    topography_object: Points | Grid2D | None = None
    topography: FloatData | float | None = None
    active_model: BooleanData | IntegerData | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one(cls, data):
        if all(v is None for v in data.values()):
            raise ValueError("Must provide either topography or active model.")
        return data

    @model_validator(mode="before")
    @classmethod
    def topo_grid_must_have_elevation_channel(cls, data):
        if isinstance(data.get("topography_object", None), Grid2D):
            if data.get("topography", None) is None:
                raise ValueError(
                    "Grid2D topography must be accompanied by a valid elevation channel."
                )
        return data

    @model_serializer(mode="wrap")
    def serialize_model(self, handler) -> dict[str, Any]:
        result = handler(self)

        if "topography_object" not in result:
            result["topography_object"] = self.topography_object

        return result


class ComputeOptions(BaseModel):
    """
    Options related to compute resources and parallelization.

    :param distributed_workers: Distributed workers.
    :param max_chunk_size: Maximum chunk size used for parallel operations.
    :param max_ram: Maximum amount of RAM available
    :param n_cpu: Number of CPUs to use for parallel operations.
    :param n_threads: Number of threads per worker
    :param n_workers: Number of distributed workers to use.
    :param performance_report: Generate an HTML report from dask.diagnostics
    :param solver_type: Type of solver to use for the inversion.
    :param tile_spatial: Number of tiles to split the data.
    """

    distributed_workers: str | None = None
    max_chunk_size: int = 128
    max_ram: float | None = None
    n_cpu: int | None = None
    n_threads: int | None = None
    n_workers: int | None = 1
    performance_report: bool = False
    solver_type: Literal["Pardiso", "Mumps"] = "Pardiso"
    tile_spatial: int = 1


class DeprecatedOptions(BaseModel):
    """
    List of deprecated options.
    """

    beta_search: Deprecated
    chunk_by_rows: Deprecated
    ga_group: Deprecated
    gps_receivers_offset: Deprecated
    gradient_type: Deprecated
    receivers_offset_z: Deprecated
    receivers_radar_drape: Deprecated
    parallelized: Deprecated
    z_from_topo: Deprecated


Deprecations = Annotated[
    DeprecatedOptions, Field(default=DeprecatedOptions(), exclude=True)
]


class CoreOptions(Options):
    """
    Core parameters shared by inverse and forward operations.

    :param run_command: Command (module name) used to run the application from
        command line.
    :param conda_environment: Name of the conda environment used to run the
        application with all of its dependencies.
    :param inversion_type: Type of inversion.
    :param active_cells: Active cell data as either a topography surface/data or a 3D model.

    :param out_group: Output group to save results.
    :param generate_sweep: Generate sweep file instead of running the app.
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
    version: str = public_version()
    icon: str | None = None
    inversion_type: str
    documentation: str | None = None
    conda_environment: str = "simpeg_drivers"
    run_command: str = "simpeg_drivers.driver"
    mesh: Octree | Grid2D | DrapeModel | None = None
    active_cells: ActiveCellsOptions
    compute: ComputeOptions = ComputeOptions()
    out_group: SimPEGGroup | UIJsonGroup | None = None
    generate_sweep: bool = False
    workspace_geoh5: Path | None = Field(
        default=None,
        exclude=True,
    )
    # List of deprecated parameters
    deprecations: Deprecations

    @property
    def components(self) -> list[str]:
        """Return list of component names."""
        return [self._component_name(k) for k in self.__dict__ if "channel" in k]

    def _component_name(self, component: str) -> str:
        """Strip the '_channel' and '_channel_bool' suffixes from data name."""
        return "_".join(
            [k for k in component.split("_") if k not in ["channel", "bool"]]
        )

    @field_validator("mesh", mode="before")
    @classmethod
    def mesh_cannot_be_rotated(cls, value: Octree):
        if isinstance(value, Octree) and value.rotation not in [0.0, None]:
            raise ValueError(
                "Rotated meshes are not supported. Please use a mesh with an angle of 0.0."
            )
        return value

    @property
    def workpath(self):
        return Path(self.geoh5.h5file).parent

    @property
    def padding_cells(self) -> int:
        """
        Default padding cells used for tiling.
        """
        # Keep whole mesh for 1 tile
        if self.compute.tile_spatial == 1:
            return 100

        return 4 if self.inversion_type in ["fdem", "tdem"] else 6

    def _create_input_file_from_attributes(self) -> InputFile:
        ifile = super()._create_input_file_from_attributes()
        ifile.set_data_value("version", public_version())
        return ifile


class ModelOptions(BaseModel):
    """
    Base class for model parameters.

    :param starting_model: Starting model.
    :param reference_model: Reference model.
    :param lower_bound: Lower bound.
    :param upper_bound: Upper bound.
    :param alpha_s: Scale on the reference model.
    :param length_scale_x: Length scale along the u-direction.
    :param length_scale_y: Length scale along the v-direction.
    :param length_scale_z: Length scale along the z-direction.
    :param gradient_rotation: Property group for gradient rotation angles.
    :param s_norm: Norm applied on the reference model.
    :param x_norm: Norm applied on the smoothing along the u-direction.
    :param y_norm: Norm applied on the smoothing along the v-direction.
    :param z_norm: Norm applied on the smoothing along the w-direction.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    # Model options
    starting_model: float | FloatData
    reference_model: float | FloatData | None = None
    lower_bound: float | FloatData | None = None
    upper_bound: float | FloatData | None = None

    # Model values for regularization
    alpha_s: float | FloatData | None = 1.0
    length_scale_x: float | FloatData = 1.0
    length_scale_y: float | FloatData | None = 1.0
    length_scale_z: float | FloatData = 1.0
    gradient_rotation: PropertyGroup | None = None

    # Model values for IRLS
    s_norm: float | FloatData | None = 0.0
    x_norm: float | FloatData = 2.0
    y_norm: float | FloatData | None = 2.0
    z_norm: float | FloatData = 2.0

    @property
    def gradient_direction(self) -> np.ndarray:
        if self.gradient_orientations is None:
            return None
        return self.gradient_orientations[:, 0]

    @property
    def gradient_dip(self) -> np.ndarray:
        if self.gradient_orientations is None:
            return None
        return self.gradient_orientations[:, 1]

    @property
    def gradient_orientations(self) -> tuple(float, float):
        """
        Direction and dip angles for rotated gradient regularization.

        Angles are in radians and are clockwise from North for direction
        and clockwise from horizontal for dip.
        """

        if self.gradient_rotation is not None:
            orientations = direction_and_dip(self.gradient_rotation)

            return np.deg2rad(orientations)

        return None


class ConductivityModelOptions(ModelOptions):
    """
    Options for the conductivity model used in all of EM methods.
    """

    model_type: Literal["Conductivity (S/m)", "Resistivity (Ohm-m)"] = (
        "Conductivity (S/m)"
    )
    conductivity_model: float | FloatData | None = Field(
        None,
        validation_alias=AliasChoices("background_conductivity", "conductivity_model"),
    )


class BaseForwardOptions(CoreOptions):
    """
    Base class for forward parameters.

    See CoreData class docstring for addition parameters descriptions.

    :param data_object: Data object containing the survey data.
    :param models: Model options for the forward simulation.
    """

    forward_only: bool = True
    data_object: Points
    models: ModelOptions

    @property
    def active_components(self) -> list[str]:
        """Return list of active components."""
        return [k for k in self.components if getattr(self, f"{k}_channel_bool")]

    @property
    def data(self) -> InversionDataDict:
        """Return dictionary of data components and associated values."""
        return dict.fromkeys(self.active_components)


class CoolingSceduleOptions(BaseModel):
    """
    Options controlling the trade-off schedule between data misfit and
    model regularization.

    :param chi_factor: Target chi factor for the data misfit.  Input value will be
        adjusted to account for the number of finite data so that factor used will
        be smaller if the data contains nan values.
    :param cooling_factor: Factor by which the regularization parameter is reduced.
    :param cooling_rate: Rate at which the regularization parameter is reduced.
    :param initial_beta: Initial regularization parameter.
    :param initial_beta_ratio: Initial ratio of regularization to data misfit.
    """

    chi_factor: float = 1.0
    cooling_factor: float = Field(
        2.0, validation_alias=AliasChoices("cooling_factor", "coolingFactor")
    )
    cooling_rate: int = Field(
        1, validation_alias=AliasChoices("cooling_rate", "coolingRate")
    )
    initial_beta: float | None = None
    initial_beta_ratio: float | None = 100.0


class DirectiveOptions(BaseModel):
    """
    Directive options for inversion.

    :param auto_scale_misfits: Automatically scale misfits of sub objectives.
    :param beta_search: Beta search.
    :param every_iteration_bool: Update the sensitivity weights every iteration.
    :param save_sensitivities: Save sensitivities to file.
    :param sens_wts_threshold: Threshold for sensitivity weights.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    auto_scale_misfits: bool = False
    every_iteration_bool: bool = True
    save_sensitivities: bool = False
    sens_wts_threshold: float | None = 1e-0


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


class EMDataMixin:
    """
    Mixin class to add data and uncertainty access from property groups.
    """

    data_object: BaseEMSurvey

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
            return dict.fromkeys(frequencies)

        group = next(
            k for k in self.data_object.property_groups if k.uid == property_group.uid
        )
        data = {
            freq: self.geoh5.get_entity(p)[0].values
            for freq, p in zip(frequencies, group.properties, strict=False)
        }
        return data


class IRLSOptions(BaseModel):
    """
    IRLS (Iteratively Reweighted Least Squares) options for inversion.

    :param beta_tol: Tolerance for the beta parameter.
    :param epsilon_cooling_factor: Factor by which the epsilon value is reduced
    :param max_irls_iterations: Maximum number of IRLS iterations.
    :param percentile: Percentile of the model values used to compute the initial epsilon value.
    :param starting_chi_factor: Starting chi factor for IRLS.  Input value will be adjusted to
        account for the number of finite data so that factor used will be smaller if the data
        contains nan values.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    beta_tol: float = 0.5
    epsilon_cooling_factor: float = Field(
        1.2, validation_alias=AliasChoices("epsilon_cooling_factor", "coolEpsFact")
    )
    max_irls_iterations: int = 25
    percentile: float = Field(
        95, validation_alias=AliasChoices("percentile", "prctile")
    )
    starting_chi_factor: float = 1.0


class LineSelectionOptions(BaseModel):
    """
    Line selection parameters for 2D inversions.

    :param line_id: Line identifier for simulation/inversion.
    :param line_object: Reference data categorizing survey by line ids.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    line_id: int = 1
    line_object: ReferencedData

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


class OptimizationOptions(BaseModel):
    """
    Optimization parameters for inversion.

    :param f_min_change: F min change.
    :param max_cg_iterations: Maximum CG iterations.
    :param max_global_iterations: Maximum global iterations.
    :param max_line_search_iterations: Maximum line search iterations.
    :param tol_cg: Tolerance CG.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    f_min_change: float = 1e-2
    max_cg_iterations: int = 30
    max_global_iterations: int = 50
    max_line_search_iterations: int = 20
    tol_cg: float = 1e-4


class BaseInversionOptions(CoreOptions):
    """
    Base class for inversion parameters.

    See CoreData class docstring for addition parameters descriptions.

    :param name: Name of the inversion.
    :param title: Title of the inversion.
    :param run_command: Command (module name) used to run the application from
        command line.
    :param forward_only: If True, only run the forward simulation.
    :param conda_environment: Name of the conda environment used to run the program
    :param data_object: Data object containing the survey data.
    :param models: Model options for the inversion.
    :param regularization: Options specific to the regularization function.
    :param irls: Options specific to the IRLS (Iteratively Reweighted Least Squares) directive.
    :param directives: Additional directives to be used in the inversion.
    :param cooling_schedule: Options controlling the trade-off schedule between data misfit and model regularization.
    :param optimization: Options for the optimization algorithm used in the inversion.
    :param store_sensitivities: Where to store sensitivities, either in RAM or on disk.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    name: ClassVar[str] = "Inversion"

    title: str = "Geophysical inversion"
    run_command: str = "simpeg_drivers.driver"

    forward_only: bool = False
    conda_environment: str = "simpeg_drivers"

    data_object: Points
    models: ModelOptions
    irls: IRLSOptions = IRLSOptions()
    directives: DirectiveOptions = DirectiveOptions()
    cooling_schedule: CoolingSceduleOptions = CoolingSceduleOptions()
    optimization: OptimizationOptions = OptimizationOptions()

    store_sensitivities: str = "ram"

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
        return {None: data}

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
            data *= np.ones_like(self.component_data(component)[None])

        return {None: data}
