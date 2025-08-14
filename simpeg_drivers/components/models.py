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

from typing import TYPE_CHECKING

import numpy as np
from geoapps_utils.driver.driver import BaseDriver
from geoapps_utils.utils.numerical import weighted_average
from geoapps_utils.utils.transformations import rotate_xyz
from geoh5py.data import NumericData
from simpeg.utils.mat_utils import (
    cartesian2amplitude_dip_azimuth,
    dip_azimuth2cartesian,
    mkvc,
)


if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver


MODEL_TYPES = [
    "starting",
    "reference",
    "lower_bound",
    "upper_bound",
    "conductivity",
    "alpha_s",
    "length_scale_x",
    "length_scale_y",
    "length_scale_z",
    "gradient_dip",
    "gradient_direction",
    "s_norm",
    "x_norm",
    "y_norm",
    "z_norm",
]


class InversionModelCollection:
    """
    Collection of inversion models.

    Methods
    -------
    remove_air: Use active cells vector to remove air cells from model.

    """

    model_types = MODEL_TYPES

    def __init__(self, driver: InversionDriver):
        """
        :param driver: Parental InversionDriver class.
        """
        self._active_cells: np.ndarray | None = None
        self._driver = driver
        self.is_sigma = self.driver.params.physical_property == "conductivity"
        is_vector = (
            True if self.driver.params.inversion_type == "magnetic vector" else False
        )
        self._starting = InversionModel(driver, "starting", is_vector=is_vector)
        self._reference = InversionModel(driver, "reference", is_vector=is_vector)
        self._lower_bound = InversionModel(driver, "lower_bound", is_vector=is_vector)
        self._upper_bound = InversionModel(driver, "upper_bound", is_vector=is_vector)
        self._conductivity = InversionModel(driver, "conductivity", is_vector=is_vector)
        self._alpha_s = InversionModel(driver, "alpha_s", is_vector=is_vector)
        self._length_scale_x = InversionModel(
            driver, "length_scale_x", is_vector=is_vector
        )
        self._length_scale_y = InversionModel(
            driver, "length_scale_y", is_vector=is_vector
        )
        self._length_scale_z = InversionModel(
            driver, "length_scale_z", is_vector=is_vector
        )
        self._gradient_dip = InversionModel(
            driver, "gradient_dip", trim_active_cells=False
        )
        self._gradient_direction = InversionModel(
            driver, "gradient_direction", trim_active_cells=False
        )
        self._s_norm = InversionModel(driver, "s_norm", is_vector=is_vector)
        self._x_norm = InversionModel(driver, "x_norm", is_vector=is_vector)
        self._y_norm = InversionModel(driver, "y_norm", is_vector=is_vector)
        self._z_norm = InversionModel(driver, "z_norm", is_vector=is_vector)

    @property
    def n_active(self) -> int:
        """Number of active cells."""
        return int(self.active_cells.sum())

    @property
    def driver(self):
        """
        Parental InversionDriver class.
        """
        return self._driver

    @property
    def active_cells(self):
        """Active cells vector."""
        if self._active_cells is None:
            self.active_cells = self.driver.inversion_topography.active_cells(
                self.driver.inversion_mesh, self.driver.inversion_data
            )
        return self._active_cells

    @active_cells.setter
    def active_cells(self, active_cells: np.ndarray | NumericData | None):
        if self._active_cells is not None:
            raise ValueError("'active_cells' can only be set once.")

        if active_cells is None:
            return

        if isinstance(active_cells, NumericData):
            active_cells = active_cells.values.astype(bool)

        if not isinstance(active_cells, np.ndarray) or active_cells.dtype != bool:
            raise ValueError("active_cells must be a boolean numpy array.")

        permutation = self.driver.inversion_mesh.permutation
        self.edit_ndv_model(permutation.T @ active_cells)
        self.remove_air(active_cells)
        self.driver.inversion_mesh.entity.add_data(
            {
                "active_cells": {
                    "values": permutation.T @ active_cells,
                    "primitive_type": "boolean",
                }
            }
        )
        self._active_cells = active_cells

    @property
    def starting(self) -> np.ndarray | None:
        if self._starting.model is None:
            return None

        mstart = self._starting.model.copy()

        if mstart is not None and self.is_sigma:
            if getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)":
                mstart = 1 / mstart

            mstart = np.log(mstart)

        return mstart

    @property
    def reference(self) -> np.ndarray | None:
        mref = self._reference.model

        if self.driver.params.forward_only:
            return mref

        if mref is None or (self.is_sigma and all(mref == 0)):
            self.driver.params.alpha_s = 0.0

            return None

        ref_model = mref.copy()

        if (
            self.is_sigma
            and getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)"
        ):
            ref_model = 1 / ref_model

        ref_model = np.log(ref_model) if self.is_sigma else ref_model

        return ref_model

    @property
    def lower_bound(self) -> np.ndarray | None:
        if (
            getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)"
            and self.is_sigma
        ):
            bound_model = self._upper_bound.model
        else:
            bound_model = self._lower_bound.model

        if (
            self.driver.params.inversion_type == "magnetic vector"
            and self._upper_bound.model is not None
        ):
            bound_model = -self._upper_bound.model

        if bound_model is None:
            return -np.inf

        lbound = bound_model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(lbound)

            if getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)":
                lbound[is_finite] = 1 / lbound[is_finite]

            lbound[is_finite] = np.log(lbound[is_finite])

        return lbound

    @property
    def upper_bound(self) -> np.ndarray | None:
        if (
            getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)"
            and self.is_sigma
        ):
            bound_model = self._lower_bound.model
        else:
            bound_model = self._upper_bound.model

        if bound_model is None:
            return np.inf

        ubound = bound_model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(ubound)

            if getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)":
                ubound[is_finite] = 1 / ubound[is_finite]

            ubound[is_finite] = np.log(ubound[is_finite])

        return ubound

    @property
    def conductivity(self) -> np.ndarray | None:
        if self._conductivity.model is None:
            return None

        background_sigma = self._conductivity.model.copy()

        if background_sigma is not None:
            if getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)":
                background_sigma = 1 / background_sigma

            # Don't apply log if IP inversion
            if self.is_sigma:
                background_sigma = np.log(background_sigma)

        return background_sigma

    @property
    def alpha_s(self) -> np.ndarray | None:
        if self._alpha_s.model is None:
            return None

        return self._alpha_s.model.copy()

    @property
    def length_scale_x(self) -> np.ndarray | None:
        if self._length_scale_x.model is None:
            return None

        return self._length_scale_x.model.copy()

    @property
    def length_scale_y(self) -> np.ndarray | None:
        if self._length_scale_y.model is None:
            return None

        return self._length_scale_y.model.copy()

    @property
    def length_scale_z(self) -> np.ndarray | None:
        if self._length_scale_z.model is None:
            return None

        return self._length_scale_z.model.copy()

    @property
    def gradient_dip(self) -> np.ndarray | None:
        if self._gradient_dip.model is None:
            return None

        return self._gradient_dip.model.copy()

    @property
    def gradient_direction(self) -> np.ndarray | None:
        if self._gradient_direction.model is None:
            return None

        return self._gradient_direction.model.copy()

    @property
    def s_norm(self) -> np.ndarray | None:
        if self._s_norm.model is None:
            return None

        s_norm = self._s_norm.model.copy()
        return s_norm

    @property
    def x_norm(self) -> np.ndarray | None:
        if self._x_norm.model is None:
            return None

        x_norm = self._x_norm.model.copy()
        return x_norm

    @property
    def y_norm(self) -> np.ndarray | None:
        if self._y_norm.model is None:
            return None

        y_norm = self._y_norm.model.copy()
        return y_norm

    @property
    def z_norm(self) -> np.ndarray | None:
        if self._z_norm.model is None:
            return None

        z_norm = self._z_norm.model.copy()
        return z_norm

    def _model_method_wrapper(self, method, name=None, **kwargs):
        """wraps individual model's specific method and applies in loop over model types."""
        returned_items = {}
        for mtype in MODEL_TYPES:
            model = getattr(self, f"_{mtype}")
            if model.model is not None:
                f = getattr(model, method)
                returned_items[mtype] = f(**kwargs)

        if name is not None:
            return returned_items[name]

    def remove_air(self, active_cells: np.ndarray):
        """Use active cells vector to remove air cells from model"""
        self._model_method_wrapper("remove_air", active_cells=active_cells)

    def permute_2_octree(self, name):
        """
        Reorder model values stored in cell centers of a TreeMesh to
        their original octree mesh sorting.

        :param: name: model type name ("starting", "reference",
            "lower_bound", or "upper_bound").

        :return: Vector of model values reordered for octree mesh.
        """
        return self._model_method_wrapper("permute_2_octree", name=name)

    def edit_ndv_model(self, actives: np.ndarray):
        """
        Change values in models recorded in geoh5 for no-data-values.

        :param actives: Array of bool defining the air: False | ground: True.
        """
        return self._model_method_wrapper("edit_ndv_model", name=None, model=actives)


class InversionModel:
    """
    A class for constructing and storing models defined on the cell centers
    of an inversion mesh.

    Methods
    -------
    remove_air: Use active cells vector to remove air cells from model.
    """

    def __init__(
        self,
        driver: InversionDriver,
        model_type: str,
        is_vector: bool = False,
        trim_active_cells: bool = True,
    ):
        """
        :param driver: InversionDriver object.
        :param model_type: Type of inversion model, can be any of MODEL_TYPES.
        :param is_vector: If True, model is a vector.
        :param trim_active_cells: If True, remove air cells from model.
        """
        self.driver = driver
        self.model_type = model_type
        self.model: np.ndarray | None = None
        self.is_vector = is_vector
        self.trim_active_cells = trim_active_cells
        self._initialize()

    def _initialize(self):
        """
        Build the model vector from params data.

        If params.inversion_type is "magnetic vector" and no inclination/declination
        are provided, then values are projected onto the direction of the
        inducing field.
        """
        if self.model_type in ["starting", "reference", "conductivity"]:
            model = self._get(self.model_type + "_model")

            if self.is_vector:
                inclination = self._get(self.model_type + "_inclination")
                declination = self._get(self.model_type + "_declination")

                if inclination is None:
                    inclination = (
                        np.ones(self.driver.inversion_mesh.n_cells)
                        * self.driver.params.inducing_field_inclination
                    )

                if declination is None:
                    declination = (
                        np.ones(self.driver.inversion_mesh.n_cells)
                        * self.driver.params.inducing_field_declination
                    )

                inclination[np.isnan(inclination)] = 0
                declination[np.isnan(declination)] = 0
                field_vecs = dip_azimuth2cartesian(
                    inclination,
                    declination,
                )

                if model is not None:
                    model += 1e-8  # make sure the incl/decl don't zero out
                    model = (field_vecs.T * model).T

        else:
            model = self._get(self.model_type)

            if (
                model is not None
                and self.is_vector
                and model.shape[0] == self.driver.inversion_mesh.n_cells
            ):
                model = np.tile(model, 3 if self.is_vector else 1)

        if model is not None:
            self.model = mkvc(model)
            self.save_model()

    def remove_air(self, active_cells):
        """Use active cells vector to remove air cells from model"""

        if self.model is not None and self.trim_active_cells:
            self.model = self.model[np.tile(active_cells, 3 if self.is_vector else 1)]

    def permute_2_octree(self) -> np.ndarray | None:
        """
        Reorder model values stored in cell centers of a TreeMesh to
        its original octree mesh order.

        :return: Vector of model values reordered for octree mesh.
        """
        if self.model is None:
            return None

        if self.is_vector:
            return mkvc(
                self.driver.inversion_mesh.permutation.T
                @ self.model.reshape((-1, 3), order="F")
            )
        return self.driver.inversion_mesh.permutation.T @ self.model

    def save_model(self):
        """Resort model to the octree object's ordering and save to workspace."""

        remapped_model = self.permute_2_octree()
        if remapped_model is None:
            return

        if self.is_vector:
            if self.model_type in ["starting", "reference"]:
                aid = cartesian2amplitude_dip_azimuth(remapped_model)
                aid[np.isnan(aid[:, 0]), 1:] = np.nan
                self.driver.inversion_mesh.entity.add_data(
                    {f"{self.model_type}_inclination": {"values": aid[:, 1]}}
                )
                self.driver.inversion_mesh.entity.add_data(
                    {f"{self.model_type}_declination": {"values": aid[:, 2]}}
                )
                remapped_model = aid[:, 0]
            elif "norm" in self.model_type:
                remapped_model = np.mean(
                    remapped_model.reshape((-1, 3), order="F"), axis=1
                )
            else:
                remapped_model = np.linalg.norm(
                    remapped_model.reshape((-1, 3), order="F"), axis=1
                )

        model_type = self.model_type
        if (
            model_type == "conductivity"
            and getattr(self.driver.params, "model_type", None) == "Resistivity (Ohm-m)"
        ):
            model_type = "resistivity"

        self.driver.inversion_mesh.entity.add_data(
            {f"{model_type}_model": {"values": remapped_model}}
        )

    def edit_ndv_model(self, model):
        """Change values to NDV on models and save to workspace."""
        for field in ["model", "inclination", "declination"]:
            model_type = self.model_type
            if (
                model_type == "conductivity"
                and getattr(self.driver.params, "model_type", None)
                == "Resistivity (Ohm-m)"
            ):
                model_type = "resistivity"

            data_obj = self.driver.inversion_mesh.entity.get_data(
                f"{model_type}_{field}"
            )
            if (
                any(data_obj)
                and isinstance(data_obj[0], NumericData)
                and data_obj[0].values is not None
            ):
                values = data_obj[0].values.copy()
                values[~model.astype(bool)] = np.nan
                data_obj[0].values = values

    def _get(self, name: str) -> np.ndarray | None:
        """
        Return model vector from value stored in params class.

        :param name: model name as stored in self.driver.params
        :return: vector with appropriate size for problem.
        """

        if hasattr(self.driver.params, name):
            model = getattr(self.driver.params, name)

            if "reference" in name and model is None:
                model = self._get("starting")

            model_values = self._get_value(model)

            return model_values

        return None

    def _get_value(self, model: float | NumericData) -> np.ndarray:
        """
        Fills vector with model value to match size of inversion mesh.

        :param model: Float value to fill vector with.
        :return: Vector of model float repeated nC times, where nC is
            the number of cells in the inversion mesh.
        """
        if isinstance(model, NumericData):
            model = self.obj_2_mesh(model, self.driver.inversion_mesh.entity)
            model = self.driver.inversion_mesh.permutation @ model
        else:
            nc = self.driver.inversion_mesh.mesh.n_cells
            if isinstance(model, int | float):
                model *= np.ones(nc)

        return model

    @staticmethod
    def obj_2_mesh(data, destination) -> np.ndarray:
        """
        Interpolates obj into inversion mesh using nearest neighbors of parent.

        :param data: Data entity containing model values
        :param destination: Destination object containing locations.
        :return: Vector of values nearest neighbor interpolated into
            inversion mesh.

        """
        xyz_out = destination.locations
        xyz_in = data.parent.locations
        full_vector = weighted_average(xyz_in, xyz_out, [data.values], n=1)[0]

        return full_vector

    @property
    def model_type(self):
        return self._model_type

    @model_type.setter
    def model_type(self, v):
        if v not in MODEL_TYPES:
            msg = f"Invalid model_type: {v}. Must be one of {(*MODEL_TYPES,)}."
            raise ValueError(msg)
        self._model_type = v
