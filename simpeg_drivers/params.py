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

from copy import deepcopy
from uuid import UUID

import numpy as np
from geoapps_utils.driver.params import BaseParams
from geoh5py.data import NumericData
from geoh5py.groups import SimPEGGroup
from geoh5py.objects import Octree
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json import InputFile


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
        self._coolEps_q: bool = None
        self._coolEpsFact: float = None
        self._beta_search: bool = None
        self._starting_chi_factor: float = None
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
        self._out_group = None
        self._ga_group = None
        self._no_data_value: float = None
        self._distributed_workers = None
        self._documentation: str = ""
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
            if isinstance(val, (int, float)):
                return np.array([float(val)] * len(d))
            else:
                return d * 0.0 + 1.0  # Default
        else:
            return None

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

    def offset(self) -> tuple[list[float], UUID]:
        """Returns offset components as list and drape data."""
        offsets = [
            0,
            0,
            0 if self.receivers_offset_z is None else self.receivers_offset_z,
        ]
        is_offset = any([(k != 0) for k in offsets])
        offsets = offsets if is_offset else None
        r = self.receivers_radar_drape
        if isinstance(r, (str, UUID)):
            r = UUID(r) if isinstance(r, str) else r
            radar = self.geoh5.get_entity(r)
            radar = radar[0].values if radar else None
        else:
            radar = None
        return offsets, radar

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

    @property
    def receivers_offset_z(self):
        return self._receivers_offset_z

    @receivers_offset_z.setter
    def receivers_offset_z(self, val):
        self.setter_validator("receivers_offset_z", val)

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

    @property
    def coolEpsFact(self):
        return self._coolEpsFact

    @coolEpsFact.setter
    def coolEpsFact(self, val):
        self.setter_validator("coolEpsFact", val)

    @property
    def beta_search(self):
        return self._beta_search

    @beta_search.setter
    def beta_search(self, val):
        self.setter_validator("beta_search", val)

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
