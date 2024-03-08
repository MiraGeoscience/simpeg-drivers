#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
from discretize import TreeMesh
from geoapps_utils.numerical import weighted_average
from geoapps_utils.transformations import rotate_xyz
from geoh5py.data import NumericData
from SimPEG.utils.mat_utils import (
    cartesian2amplitude_dip_azimuth,
    dip_azimuth2cartesian,
    mkvc,
)

from simpeg_drivers.utils.mesh import (
    floating_active,
    get_containing_cells,
    get_neighbouring_cells,
)
from simpeg_drivers.utils.utils import active_from_xyz

if TYPE_CHECKING:
    from geoh5py.objects import DrapeModel

    from simpeg_drivers.components.data import InversionData
    from simpeg_drivers.driver import InversionDriver


class InversionModelCollection:
    """
    Collection of inversion models.

    Methods
    -------
    remove_air: Use active cells vector to remove air cells from model.

    """

    model_types = [
        "starting",
        "reference",
        "lower_bound",
        "upper_bound",
        "conductivity",
    ]

    def __init__(self, driver: InversionDriver):
        """
        :param driver: Parental InversionDriver class.
        """
        self._driver: InversionDriver = driver
        self._active_cells = None

        self.is_sigma = self.driver.params.physical_property == "conductivity"

        self.is_vector = False

        if self.driver.params.inversion_type == "magnetic vector":
            self.is_vector = True

        self._starting = InversionModel(driver, "starting", is_vector=self.is_vector)
        self._reference = InversionModel(driver, "reference", is_vector=self.is_vector)
        self._lower_bound = InversionModel(
            driver, "lower_bound", is_vector=self.is_vector
        )
        self._upper_bound = InversionModel(
            driver, "upper_bound", is_vector=self.is_vector
        )
        self._conductivity = InversionModel(
            driver, "conductivity", is_vector=self.is_vector
        )

    @property
    def n_active(self) -> int:
        """Number of active cells."""
        return int(self.active_cells.sum())

    @property
    def driver(self) -> InversionDriver:
        """Parental InversionDriver class."""
        return self._driver

    @property
    def active_cells(self):
        """Active cells vector."""
        if self._active_cells is None:
            # Build active cells array and reduce models active set
            self.active_cells = self.get_active_cells()
        return self._active_cells

    @active_cells.setter
    def active_cells(self, active_cells):
        if self._active_cells is not None:
            raise ValueError("'active_cells' can only be set once.")

        if not isinstance(active_cells, np.ndarray) or active_cells.dtype != bool:
            raise ValueError("active_cells must be a boolean numpy array.")

        permutation = self.driver.inversion_mesh.permutation
        self.edit_ndv_model(active_cells[permutation])
        self.remove_air(active_cells)
        self.driver.inversion_mesh.entity.add_data(
            {"active_cells": {"values": active_cells[permutation].astype(np.int32)}}
        )
        self._active_cells = active_cells

    @property
    def starting(self) -> np.ndarray:
        if self._starting.model is None:
            raise ValueError("Starting model is not defined.")

        mstart = self._starting.model.copy()

        if mstart is not None and self.is_sigma:
            mstart = np.log(mstart)

        return mstart

    @property
    def reference(self) -> np.ndarray | None:
        mref = self._reference.model

        if self.driver.params.forward_only:
            return mref

        if mref is None or (self.is_sigma and all(mref == 0)):
            self.driver.params.alpha_s = 0.0

            return self.starting.copy()

        ref_model = mref.copy()
        ref_model = np.log(ref_model) if self.is_sigma else ref_model

        return ref_model

    @property
    def lower_bound(self) -> np.ndarray | None:
        if self._lower_bound.model is None:
            return -np.inf

        lbound = self._lower_bound.model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(lbound)
            lbound[is_finite] = np.log(lbound[is_finite])

        return lbound

    @property
    def upper_bound(self) -> np.ndarray | None:
        if self._upper_bound.model is None:
            return np.inf

        ubound = self._upper_bound.model.copy()

        if self.is_sigma:
            is_finite = np.isfinite(ubound)
            ubound[is_finite] = np.log(ubound[is_finite])

        return ubound

    @property
    def conductivity(self) -> np.ndarray | None:
        if self._conductivity.model is None:
            return None

        mstart = self._conductivity.model.copy()

        if mstart is not None and self.is_sigma:
            mstart = np.log(mstart)

        return mstart

    def _model_method_wrapper(self, method, name=None, **kwargs):
        """wraps individual model's specific method and applies in loop over model types."""
        if name is None:
            return None

        returned_items = {}
        for mtype in self.model_types:
            model = getattr(self, f"_{mtype}")
            if model.model is not None:
                f = getattr(model, method)
                returned_items[mtype] = f(**kwargs)

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

    def permute_2_treemesh(self, model, name):
        """
        Reorder model values stored in cell centers of an octree mesh to
        TreeMesh sorting.

        :param model: octree sorted model.
        :param name: model type name ("starting", "reference",
            "lower_bound", or "upper_bound").

        :return: Vector of model values reordered for TreeMesh.
        """
        return self._model_method_wrapper("permute_2_treemesh", name=name, model=model)

    def edit_ndv_model(self, actives: np.ndarray):
        """
        Change values in models recorded in geoh5 for no-data-values.

        :param actives: Array of bool defining the air: False | ground: True.
        """
        return self._model_method_wrapper("edit_ndv_model", name=None, model=actives)

    def get_active_cells(self) -> np.ndarray:
        """
        Return mask that restricts models to set of earth cells.

        :param: mesh: inversion mesh.
        :return: active_cells: Mask that restricts a model to the set of
            earth cells that are active in the inversion (beneath topography).
        """
        active_cells = active_from_xyz(
            self.driver.inversion_mesh.entity,
            self.driver.inversion_topography.locations,
            grid_reference="bottom" if self.driver.force_to_surface else "center",
        )
        active_cells = active_cells[np.argsort(self.driver.inversion_mesh.permutation)]

        if self.driver.force_to_surface:
            active_cells = self.expand_actives(
                active_cells,
                self.driver.inversion_mesh.mesh,
                self.driver.inversion_data,
            )

            if floating_active(self.driver.inversion_mesh.mesh, active_cells):
                warnings.warn(
                    "Active cell adjustment has created a patch of active cells in the air, "
                    "likely due to a faulty survey location."
                )

        return active_cells

    @staticmethod
    def expand_actives(
        active_cells: np.ndarray, mesh: TreeMesh | DrapeModel, data: InversionData
    ) -> np.ndarray:
        """
        Expand active cells to ensure receivers are within active cells.

        :param active_cells: Mask that restricts a model to the set of
        :param mesh: Inversion mesh.
        :param data: Inversion data.

        :return: active_cells: Mask that restricts a model to the set of
        """
        containing_cells = get_containing_cells(mesh, data)
        active_cells[containing_cells] = True

        # Apply extra active cells to ensure connectivity for tree meshes
        if isinstance(mesh, TreeMesh):
            neighbours = get_neighbouring_cells(mesh, containing_cells)
            neighbours_xy = np.r_[neighbours[0] + neighbours[1]]

            # Make sure the new actives are connected to the old actives
            new_actives = ~active_cells[neighbours_xy]
            if np.any(new_actives):
                neighbours = get_neighbouring_cells(mesh, neighbours_xy[new_actives])
                active_cells[np.r_[neighbours[2][0]]] = True  # z-axis neighbours

            active_cells[neighbours_xy] = True  # xy-axis neighbours

        return active_cells


class InversionModel:
    """
    A class for constructing and storing models defined on the cell centers
    of an inversion mesh.

    Methods
    -------
    remove_air: Use active cells vector to remove air cells from model.
    """

    model_types = [
        "starting",
        "reference",
        "lower_bound",
        "upper_bound",
        "conductivity",
    ]

    def __init__(
        self,
        driver: InversionDriver,
        model_type: str,
        is_vector: bool = False,
    ):
        """
        :param driver: InversionDriver object.
        :param model_type: Type of inversion model, can be any of "starting", "reference",
            "lower_bound", "upper_bound".
        """
        self.driver = driver
        self.model_type = model_type
        self.model: np.ndarray | None = None
        self.is_vector = is_vector

        self.n_blocks = 1
        if is_vector:
            self.n_blocks = 3

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

                if self.driver.inversion_mesh.rotation is not None:
                    declination += self.driver.inversion_mesh.rotation["angle"]

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
                model = np.tile(model, self.n_blocks)

        if model is not None:
            self.model = mkvc(model)
            self.save_model()

    def remove_air(self, active_cells):
        """Use active cells vector to remove air cells from model"""

        if self.model is not None:
            self.model = self.model[np.tile(active_cells, self.n_blocks)]

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
                self.model.reshape((-1, 3), order="F")[
                    self.driver.inversion_mesh.permutation, :
                ]
            )
        return self.model[self.driver.inversion_mesh.permutation]

    def permute_2_treemesh(self, model: np.ndarray) -> np.ndarray:
        """
        Reorder model values stored in cell centers of an octree mesh to
        TreeMesh order in self.driver.inversion_mesh.

        :param model: octree sorted model
        :return: Vector of model values reordered for TreeMesh.
        """
        return model[np.argsort(self.driver.inversion_mesh.permutation)]

    def save_model(self):
        """Resort model to the octree object's ordering and save to workspace."""

        remapped_model = self.permute_2_octree()
        if remapped_model is None:
            return

        if self.is_vector:
            if self.model_type in ["starting", "reference"]:
                aid = cartesian2amplitude_dip_azimuth(remapped_model)
                aid[np.isnan(aid[:, 0]), 1:] = np.nan
                entity = self.driver.inversion_mesh.entity.add_data(
                    {f"{self.model_type}_inclination": {"values": aid[:, 1]}}
                )
                setattr(self.driver.params, f"{self.model_type}_inclination", entity)
                entity = self.driver.inversion_mesh.entity.add_data(
                    {f"{self.model_type}_declination": {"values": aid[:, 2]}}
                )
                setattr(self.driver.params, f"{self.model_type}_declination", entity)
                remapped_model = aid[:, 0]
            else:
                remapped_model = np.linalg.norm(
                    remapped_model.reshape((-1, 3), order="F"), axis=1
                )

        entity = self.driver.inversion_mesh.entity.add_data(
            {f"{self.model_type}_model": {"values": remapped_model}}
        )
        model_type = self.model_type

        # TODO: Standardize names for upper_model and lower_model
        if model_type in ["starting", "reference", "conductivity"]:
            model_type += "_model"

        setattr(self.driver.params, model_type, entity)

    def edit_ndv_model(self, model):
        """Change values to NDV on models and save to workspace."""
        for field in ["model", "inclination", "declination"]:
            data_obj = self.driver.inversion_mesh.entity.get_data(
                f"{self.model_type}_{field}"
            )
            if (
                any(data_obj)
                and isinstance(data_obj[0], NumericData)
                and data_obj[0].values is not None
            ):
                values = data_obj[0].values.copy()
                values[~model] = np.nan
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
            model = self._obj_2_mesh(model.values, model.parent)

        else:
            nc = self.driver.inversion_mesh.n_cells
            if isinstance(model, (int, float)):
                model *= np.ones(nc)

        return model

    def _obj_2_mesh(self, obj, parent) -> np.ndarray:
        """
        Interpolates obj into inversion mesh using nearest neighbors of parent.

        :param obj: geoh5 entity object containing model data
        :param parent: parent geoh5 entity to model containing location data.
        :return: Vector of values nearest neighbor interpolated into
            inversion mesh.

        """
        xyz_out = self.driver.inversion_mesh.entity.centroids

        if hasattr(parent, "centroids"):
            xyz_in = parent.centroids
            if self.driver.inversion_mesh.rotation is not None:
                xyz_out = rotate_xyz(
                    xyz_out,
                    self.driver.inversion_mesh.rotation["origin"],
                    self.driver.inversion_mesh.rotation["angle"],
                )

        else:
            xyz_in = parent.vertices

        full_vector = weighted_average(xyz_in, xyz_out, [obj], n=1)[0]

        return full_vector[np.argsort(self.driver.inversion_mesh.permutation)]

    @property
    def model_type(self):
        return self._model_type

    @model_type.setter
    def model_type(self, v):
        if v not in self.model_types:
            msg = f"Invalid 'model_type'. Must be one of {*self.model_types,}."
            raise ValueError(msg)
        self._model_type = v
