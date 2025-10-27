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
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.utils.numerical import weighted_average
from geoh5py.data import Data, FloatData, NumericData
from geoh5py.data.data_type import GeometricDataValueMapType
from geoh5py.objects import ObjectBase
from simpeg.utils.mat_utils import (
    dip_azimuth2cartesian,
    mkvc,
)


if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver


MODEL_TYPES = [
    "starting_model",
    "starting_inclination",
    "starting_declination",
    "reference_model",
    "reference_inclination",
    "reference_declination",
    "lower_bound",
    "upper_bound",
    "conductivity_model",
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
    "petrophysical_model",
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
        self.is_vector = self.driver.params.inversion_type == "magnetic vector"

        self._starting_model = InversionModel(
            driver, "starting_model", is_sigma=self.is_sigma
        )
        self._starting_inclination = InversionModel(driver, "starting_inclination")
        self._starting_declination = InversionModel(driver, "starting_declination")
        self._reference_model = InversionModel(
            driver, "reference_model", is_sigma=self.is_sigma
        )
        self._reference_inclination = InversionModel(driver, "reference_inclination")
        self._reference_declination = InversionModel(driver, "reference_declination")
        self._lower_bound = InversionModel(
            driver, "lower_bound", is_sigma=self.is_sigma
        )
        self._upper_bound = InversionModel(
            driver, "upper_bound", is_sigma=self.is_sigma
        )
        self._conductivity_model = InversionModel(
            driver, "conductivity_model", is_sigma=self.is_sigma
        )
        self._alpha_s = InversionModel(driver, "alpha_s")
        self._length_scale_x = InversionModel(driver, "length_scale_x")
        self._length_scale_y = InversionModel(driver, "length_scale_y")
        self._length_scale_z = InversionModel(driver, "length_scale_z")
        self._gradient_dip = InversionModel(
            driver, "gradient_dip", trim_active_cells=False
        )
        self._gradient_direction = InversionModel(
            driver, "gradient_direction", trim_active_cells=False
        )
        self._s_norm = InversionModel(driver, "s_norm")
        self._x_norm = InversionModel(driver, "x_norm")
        self._y_norm = InversionModel(driver, "y_norm")
        self._z_norm = InversionModel(driver, "z_norm")
        self._petrophysical_model = InversionModel(driver, "petrophysical_model")

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
    def starting_model(self) -> np.ndarray | None:
        if self._starting_model.model is None:
            return None

        mstart = self._starting_model.model.copy()

        if mstart is not None and self.is_sigma:
            if self.driver.params.models.model_type == "Resistivity (Ohm-m)":
                mstart = 1 / mstart

            mstart = np.log(mstart)

        if self.is_vector:
            field_vecs = dip_azimuth2cartesian(
                self.starting_inclination,
                self.starting_declination,
            )
            mstart = (field_vecs.T * mstart).flatten()

        return mstart

    @property
    def starting_inclination(self) -> np.ndarray | None:
        value = self._starting_inclination.model

        if value is None and self.is_vector:
            return (
                np.ones_like(self._starting_model.model)
                * self.driver.params.inducing_field_inclination
            )

        if value is not None:
            value[np.isnan(value)] = 0

        return value

    @property
    def starting_declination(self) -> np.ndarray | None:
        value = self._starting_declination.model

        if value is None and self.is_vector:
            return (
                np.ones_like(self._starting_model.model)
                * self.driver.params.inducing_field_declination
            )

        return value

    @property
    def reference_model(self) -> np.ndarray | None:
        mref = self._reference_model.model

        if self.driver.params.forward_only:
            return mref

        if mref is None or (self.is_sigma and all(mref == 0)):
            self.driver.params.alpha_s = 0.0

            return None

        ref_model = mref.copy()

        if self.is_sigma:
            if self.driver.params.models.model_type == "Resistivity (Ohm-m)":
                ref_model = 1 / ref_model

            ref_model = np.log(ref_model)

        if self.is_vector:
            field_vecs = dip_azimuth2cartesian(
                self.reference_inclination,
                self.reference_declination,
            )
            ref_model = (field_vecs.T * ref_model).flatten()

        return ref_model

    @property
    def reference_inclination(self) -> np.ndarray | None:
        value = self._reference_inclination.model

        if value is None and self.is_vector:
            return (
                np.ones(self.active_cells.sum())
                * self.driver.params.inducing_field_inclination
            )

        return value

    @property
    def reference_declination(self) -> np.ndarray | None:
        value = self._reference_declination.model

        if value is None and self.is_vector:
            return (
                np.ones(self.active_cells.sum())
                * self.driver.params.inducing_field_declination
            )

        return value

    @property
    def lower_bound(self) -> np.ndarray | None:
        if (
            self.is_sigma
            and self.driver.params.models.model_type == "Resistivity (Ohm-m)"
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
            lbound = np.full(self.n_active, -np.inf)
        else:
            lbound = bound_model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(lbound)

            if self.driver.params.models.model_type == "Resistivity (Ohm-m)":
                lbound[is_finite] = 1 / lbound[is_finite]

            lbound[is_finite] = np.log(lbound[is_finite])

        if self.is_vector:
            lbound = np.tile(lbound, 3)

        return lbound

    @property
    def upper_bound(self) -> np.ndarray | None:
        if (
            self.is_sigma
            and self.driver.params.models.model_type == "Resistivity (Ohm-m)"
        ):
            bound_model = self._lower_bound.model
        else:
            bound_model = self._upper_bound.model

        if bound_model is None:
            ubound = np.full(self.n_active, np.inf)
        else:
            ubound = bound_model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(ubound)

            if self.driver.params.models.model_type == "Resistivity (Ohm-m)":
                ubound[is_finite] = 1 / ubound[is_finite]

            ubound[is_finite] = np.log(ubound[is_finite])

        if self.is_vector:
            ubound = np.tile(ubound, 3)

        return ubound

    @property
    def conductivity_model(self) -> np.ndarray | None:
        if self._conductivity_model.model is None:
            return None

        background_sigma = self._conductivity_model.model.copy()

        if background_sigma is not None:
            if self.driver.params.models.model_type == "Resistivity (Ohm-m)":
                background_sigma = 1 / background_sigma

            # Don't apply log if IP inversion
            if self.is_sigma:
                background_sigma = np.log(background_sigma)

        return background_sigma

    @property
    def alpha_s(self) -> np.ndarray | None:
        if self._alpha_s.model is None:
            return None

        alpha = self._alpha_s.model.copy()

        if self.is_vector:
            alpha = np.tile(alpha, 3)

        return alpha

    @property
    def length_scale_x(self) -> np.ndarray | None:
        if self._length_scale_x.model is None:
            return None

        length_scale = self._length_scale_x.model.copy()

        if self.is_vector:
            length_scale = np.tile(length_scale, 3)
        return length_scale

    @property
    def length_scale_y(self) -> np.ndarray | None:
        if self._length_scale_y.model is None:
            return None

        length_scale = self._length_scale_y.model.copy()

        if self.is_vector:
            length_scale = np.tile(length_scale, 3)
        return length_scale

    @property
    def length_scale_z(self) -> np.ndarray | None:
        if self._length_scale_z.model is None:
            return None

        length_scale = self._length_scale_z.model.copy()

        if self.is_vector:
            length_scale = np.tile(length_scale, 3)
        return length_scale

    @property
    def s_norm(self) -> np.ndarray | None:
        if self._s_norm.model is None:
            return None

        s_norm = self._s_norm.model.copy()

        if self.is_vector:
            s_norm = np.tile(s_norm, 3)

        return s_norm

    @property
    def x_norm(self) -> np.ndarray | None:
        if self._x_norm.model is None:
            return None

        x_norm = self._x_norm.model.copy()

        if self.is_vector:
            x_norm = np.tile(x_norm, 3)

        return x_norm

    @property
    def y_norm(self) -> np.ndarray | None:
        if self._y_norm.model is None:
            return None

        y_norm = self._y_norm.model.copy()

        if self.is_vector:
            y_norm = np.tile(y_norm, 3)

        return y_norm

    @property
    def z_norm(self) -> np.ndarray | None:
        if self._z_norm.model is None:
            return None

        z_norm = self._z_norm.model.copy()

        if self.is_vector:
            z_norm = np.tile(z_norm, 3)

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

    @property
    def petrophysical_model(self) -> np.ndarray | None:
        if self._petrophysical_model.model is None:
            return None

        return self._petrophysical_model.model.copy()

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

    def remove_air(self, active_cells: np.ndarray):
        """Use active cells vector to remove air cells from model"""
        self._model_method_wrapper("remove_air", active_cells=active_cells)

    def permute_2_octree(self, name):
        """
        Reorder model values stored in cell centers of a TreeMesh to
        their original octree mesh sorting.

        :param: name: model type name ("starting_model", "reference_model",
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
        trim_active_cells: bool = True,
        is_sigma: bool = False,
    ):
        """
        :param driver: InversionDriver object.
        :param model_type: Type of inversion model, can be any of MODEL_TYPES.
        :param is_vector: If True, model is a vector.
        :param trim_active_cells: If True, remove air cells from model.
        """
        self.driver = driver
        self.model_type = model_type
        self.is_sigma = is_sigma
        self.model: np.ndarray | None = None
        self.trim_active_cells = trim_active_cells
        self._initialize()

    def _initialize(self):
        """
        Build the model vector from params data.

        If params.inversion_type is "magnetic vector" and no inclination/declination
        are provided, then values are projected onto the direction of the
        inducing field.
        """
        model = self._get(self.model_type)

        if model is not None:
            if self.is_sigma and np.any(model <= 0):
                raise GeoAppsError(
                    f"All values in {self.model_type} must be positive when "
                    "inversion is in log-conductivity space."
                )

            self.model = mkvc(model)

            if isinstance(self._fetch_reference(self.model_type), Data):
                self.save_model()

    def remove_air(self, active_cells):
        """Use active cells vector to remove air cells from model"""

        if self.model is not None and self.trim_active_cells:
            self.model = self.model[active_cells]

    def permute_2_octree(self) -> np.ndarray | None:
        """
        Reorder model values stored in cell centers of a TreeMesh to
        its original octree mesh order.

        :return: Vector of model values reordered for octree mesh.
        """
        if self.model is None:
            return None

        return self.driver.inversion_mesh.permutation.T @ self.model

    def save_model(self):
        """Resort model to the octree object's ordering and save to workspace."""

        remapped_model = self.permute_2_octree()
        if remapped_model is None:
            return

        model_type = self.model_type
        if (
            model_type == "conductivity_model"
            and self.driver.params.models.model_type == "Resistivity (Ohm-m)"
        ):
            model_type = "resistivity_model"

        entity_type = None
        if isinstance(self._fetch_reference(self.model_type), NumericData):
            entity_type = self._fetch_reference(self.model_type).entity_type

        self.driver.inversion_mesh.entity.add_data(
            {
                f"{model_type}": {
                    "values": remapped_model,
                    "entity_type": entity_type,
                }
            }
        )

    def edit_ndv_model(self, model):
        """Change values to NDV on models and save to workspace."""
        model_type = self.model_type
        if (
            model_type == "conductivity_model"
            and getattr(self.driver.params.models, "model_type", None)
            == "Resistivity (Ohm-m)"
        ):
            model_type = "resistivity_model"

        data_obj = self.driver.inversion_mesh.entity.get_data(model_type)
        if (
            any(data_obj)
            and isinstance(data_obj[0], NumericData)
            and data_obj[0].values is not None
        ):
            values = data_obj[0].values.copy()
            values[~model.astype(bool)] = (
                np.nan if isinstance(data_obj[0], FloatData) else 0
            )
            data_obj[0].values = values

    def _fetch_reference(self, name: str) -> NumericData | None:
        value = getattr(self.driver.params.models, name, None)
        return value

    def _get(self, name: str) -> np.ndarray | None:
        """
        Return model vector from value stored in params class.

        :param name: model name as stored in self.driver.params
        :return: vector with appropriate size for problem.
        """
        model = self._fetch_reference(name)

        if model is None:
            return None

        return self._get_value(model)

    def _get_value(self, model: float | NumericData) -> np.ndarray:
        """
        Fills vector with model value to match size of inversion mesh.

        :param model: Float value to fill vector with.
        :return: Vector of model float repeated nC times, where nC is
            the number of cells in the inversion mesh.
        """
        if isinstance(model, NumericData):
            model = self.obj_2_mesh(model, self.driver.inversion_mesh.entity)
            model = (self.driver.inversion_mesh.permutation @ model).astype(model.dtype)
        else:
            nc = self.driver.inversion_mesh.mesh.n_cells
            if isinstance(model, int | float):
                model *= np.ones(nc)

        return model

    @staticmethod
    def obj_2_mesh(data: Data, destination: ObjectBase) -> np.ndarray:
        """
        Interpolates obj into inversion mesh using nearest neighbors of parent.

        :param data: Data entity containing model values
        :param destination: Destination object containing locations.
        :return: Vector of values nearest neighbor interpolated into
            inversion mesh.

        """
        xyz_out = destination.locations
        xyz_in = data.parent.locations

        values = data.values.astype(float)

        if isinstance(data.entity_type, GeometricDataValueMapType):
            values[values == 0] = np.nan

        full_vector = weighted_average(xyz_in, xyz_out, [values], n=1)[0]

        return full_vector.astype(data.values.dtype)

    @property
    def model_type(self):
        return self._model_type

    @model_type.setter
    def model_type(self, v):
        if v not in MODEL_TYPES:
            msg = f"Invalid model_type: {v}. Must be one of {(*MODEL_TYPES,)}."
            raise ValueError(msg)
        self._model_type = v
