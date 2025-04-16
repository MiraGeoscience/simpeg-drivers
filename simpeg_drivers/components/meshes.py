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
from typing import TYPE_CHECKING

import numpy as np
from discretize import TensorMesh, TreeMesh
from geoh5py import Workspace
from geoh5py.groups import UIJsonGroup
from geoh5py.objects import DrapeModel, Octree
from octree_creation_app.driver import OctreeDriver
from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree
from scipy.sparse import csr_matrix, identity

from simpeg_drivers.options import BaseForwardOptions, BaseInversionOptions
from simpeg_drivers.utils.meshes import auto_mesh_parameters
from simpeg_drivers.utils.utils import drape_2_tensor


logger = getLogger(__name__)
if TYPE_CHECKING:
    from simpeg_drivers.components.data import InversionData
    from simpeg_drivers.components.topography import InversionTopography


# TODO: Import this from newer octree-creation-app release
def tree_levels(mesh: Octree) -> np.ndarray | None:
    """
    Convert Octree n cell indices to Treemesh level indices.

    :param mesh: Octree object with n cell index.

    :returns: Array of level indices.
    """
    if mesh.octree_cells is None:
        return None

    n_cell_dim = [mesh.u_count, mesh.v_count, mesh.w_count]
    ls = np.log2(n_cell_dim).astype(int)
    if len(set(ls)) == 1:
        max_level = ls[0]
    else:
        max_level = min(ls) + 1
    levels = max_level - np.log2(mesh.octree_cells["NCells"])

    return levels


class InversionMesh:
    """
    Retrieve octree mesh data from workspace and convert to Treemesh.

    Attributes
    ----------

    n_cells:
        Number of cells in the mesh.
    rotation :
        Rotation of original octree mesh.
    permutation:
        Permutation vector to restore cell centers or model values to
        origin octree mesh order.

    """

    def __init__(
        self,
        workspace: Workspace,
        params: BaseForwardOptions | BaseInversionOptions,
        entity: Octree | DrapeModel | None = None,
    ) -> None:
        """
        :param workspace: Workspace object containing mesh data.
        :param params: Options object containing mesh parameters.
        """
        self.workspace = workspace
        self.params = params
        self.entity = entity or self.get_entity()
        self.mesh, self._permutation = self.to_discretize(self.entity)

    def get_entity(self) -> Octree | DrapeModel:
        """
        Collects mesh data stored in geoh5 workspace into TreeMesh object.

        Handles conversion from geoh5's native octree mesh type to TreeMesh
        type required for SimPEG inversion and stores data needed to restore
        original the octree mesh type.
        """
        if self.params.mesh is None:
            logger.info(
                "No mesh provided. Creating optimized mesh from data and topography."
            )
            mesh_entity = self._auto_mesh()
        else:
            mesh_entity = self.params.mesh.copy(
                parent=self.params.out_group, copy_children=False
            )

        return mesh_entity

    def _auto_mesh(self):
        """Automate meshing based on data and topography objects."""

        params = auto_mesh_parameters(
            self.params.data_object,
            self.params.active_cells.topography_object,
            inversion_type=self.params.inversion_type,
        )
        driver = OctreeDriver(params)

        mesh = driver.run()
        return mesh.copy(parent=self.params.out_group)

    @classmethod
    def to_discretize(
        cls,
        entity: Octree | DrapeModel,
    ) -> tuple[TreeMesh | TensorMesh, np.ndarray]:
        """
        Converts mesh entity to its discretize equivalent.

        :param entity: Octree or DrapeModel object containing mesh data.

        :return: Tuple containing mesh object and permutation vector.
        """

        if isinstance(entity, Octree):
            mesh = cls.to_treemesh(entity)
            permutation = identity(entity.n_cells).tocsr()
        elif isinstance(entity, DrapeModel):
            mesh, indices = drape_2_tensor(entity, return_sorting=True)
            permutation = csr_matrix(
                (np.ones_like(indices), (np.arange(len(indices)), indices)),
                shape=(mesh.n_cells, entity.n_cells),
            )
        else:
            raise TypeError("Mesh object must be of type Octree or DrapeModel.")

        return mesh, permutation

    @property
    def mesh(self) -> TreeMesh | TensorMesh:
        """TreeMesh or TensorMesh object containing mesh data."""
        # In case the _mesh was reset by the driver.
        if self._mesh is None:
            self.mesh, self._permutation = self.to_discretize(self.entity)

        return self._mesh

    @mesh.setter
    def mesh(self, value: TreeMesh | TensorMesh | None):
        if not isinstance(value, (TreeMesh | TensorMesh | type(None))):
            raise TypeError("Attribute 'mesh' must be a TreeMesh or TensorMesh object.")

        self._mesh = value

    @property
    def n_cells(self) -> int:
        """Number of cells in the mesh."""
        return self.entity.n_cells

    @property
    def permutation(self) -> np.ndarray:
        """Permutation vector between discretize and geoh5py/DrapeModel ordering."""
        return self._permutation

    @property
    def entity(self) -> Octree | DrapeModel:
        """Octree or DrapeModel object containing mesh data."""
        return self._entity

    @entity.setter
    def entity(self, entity: Octree | DrapeModel):
        if not isinstance(entity, Octree | DrapeModel):
            raise TypeError(
                "Attribute 'entity' must be an Octree or DrapeModel object."
            )

        self._entity = entity

    @staticmethod
    def to_treemesh(octree):
        """Ensures octree mesh is in IJK order and has positive cell sizes."""

        if any(getattr(octree, f"{axis}_cell_size") < 0 for axis in "uvw"):
            mesh = InversionMesh.ensure_cell_convention(octree)
            return mesh

        mesh = octree_2_treemesh(octree)
        if not np.allclose(octree.centroids, mesh.cell_centers):
            mesh = InversionMesh.ensure_cell_convention(octree)

        return mesh

    @staticmethod
    def ensure_cell_convention(mesh: Octree) -> TreeMesh | None:
        """
        Shift origin and flip sign for negative cell size dimensions.

        :param mesh: Input octree mesh object.

        :return: Mesh object with positive cell sizes and shifted origin
            to maintain mesh geometry.
        """

        if mesh.rotation:
            raise ValueError("Cannot convert negative cell sizes for rotated mesh.")

        cell_sizes, origin = [], []
        for axis, dim in zip("xyz", "uvw", strict=True):
            n_cells = getattr(mesh, f"{dim}_count")
            cell_size = getattr(mesh, f"{dim}_cell_size")
            if cell_size < 0:
                origin.append(mesh.origin[axis] + n_cells * cell_size)
                cell_sizes.append([np.abs(cell_size)] * n_cells)
            else:
                origin.append(mesh.origin[axis])
                cell_sizes.append([cell_size] * n_cells)

        treemesh = TreeMesh(cell_sizes, origin, diagonal_balance=False)
        levels = tree_levels(mesh)
        treemesh.insert_cells(points=mesh.centroids, levels=levels, finalize=True)

        temp_workspace = Workspace()
        temp_octree = treemesh_2_octree(temp_workspace, treemesh)

        mesh.octree_cells = temp_octree.octree_cells
        mesh.origin = origin
        for dim in "uvw":
            attr = f"{dim}_cell_size"
            setattr(mesh, attr, np.abs(getattr(mesh, attr)))

        indices = treemesh.get_containing_cells(mesh.centroids)
        ind = np.argsort(indices)
        for child in mesh.children:
            if child.values is None or isinstance(child.values, np.ndarray):
                continue
            child.values = child.values[ind]

        return treemesh
