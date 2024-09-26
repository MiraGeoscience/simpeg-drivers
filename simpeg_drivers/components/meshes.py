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

from typing import TYPE_CHECKING

import numpy as np
from discretize import TensorMesh, TreeMesh
from geoh5py import Workspace
from geoh5py.objects import DrapeModel, Octree
from octree_creation_app.params import OctreeParams
from octree_creation_app.utils import octree_2_treemesh, treemesh_2_octree

from simpeg_drivers.params import InversionBaseParams
from simpeg_drivers.utils.utils import drape_2_tensor


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
        params: InversionBaseParams,
    ) -> None:
        """
        :param workspace: Workspace object containing mesh data.
        :param params: Params object containing mesh parameters.
        """
        self.workspace = workspace
        self.params = params
        self.mesh: TreeMesh | TensorMesh | None = None
        self.n_cells: int | None = None
        self.rotation: dict[str, float] | None = None
        self._permutation: np.ndarray | None = None
        self.entity: Octree | DrapeModel | None = None
        self._initialize()

    def _initialize(self) -> None:
        """
        Collects mesh data stored in geoh5 workspace into TreeMesh object.

        Handles conversion from geoh5's native octree mesh type to TreeMesh
        type required for SimPEG inversion and stores data needed to restore
        original the octree mesh type.
        """

        if self.params.mesh is None:
            raise ValueError("Must pass pre-constructed mesh.")
        else:
            self.entity = self.params.mesh.copy(
                parent=self.params.out_group, copy_children=False
            )
            self.params.mesh = self.entity

        self.uid = self.entity.uid
        self.n_cells = self.entity.n_cells

    @property
    def mesh(self) -> TreeMesh | TensorMesh:
        """TreeMesh or TensorMesh object containing mesh data."""

        if self._mesh is None:
            if isinstance(self._entity, Octree):
                self._mesh = octree_2_treemesh(self._entity)
                self._permutation = np.arange(self.entity.n_cells)

            if isinstance(self.entity, DrapeModel) and self._mesh is None:
                self._mesh, self._permutation = drape_2_tensor(
                    self.entity, return_sorting=True
                )

        return self._mesh

    @mesh.setter
    def mesh(self, value: TreeMesh | TensorMesh | None):
        if not isinstance(value, (TreeMesh | TensorMesh | type(None))):
            raise TypeError("Attribute 'mesh' must be a TreeMesh or TensorMesh object.")

        self._mesh = value

    @property
    def permutation(self) -> np.ndarray:
        """Permutation vector between discretize and geoh5py/DrapeModel ordering."""
        if self.mesh is None:
            raise ValueError("A 'mesh' must be assigned before accessing permutation.")
        return self._permutation

    @property
    def entity(self) -> Octree | DrapeModel:
        """Octree or DrapeModel object containing mesh data."""
        return self._entity

    @entity.setter
    def entity(self, val: Octree | DrapeModel):
        if not isinstance(val, Octree | DrapeModel | type(None)):
            raise TypeError(
                "Attribute 'entity' must be an Octree or DrapeModel object."
            )

        self._entity = val

        if isinstance(self._entity, Octree):
            self._permutation = np.arange(self.entity.n_cells)
            self._mesh = self.to_treemesh(self._entity)

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

        treemesh = TreeMesh(cell_sizes, origin)
        levels = tree_levels(mesh)
        treemesh.insert_cells(points=mesh.centroids, levels=levels, finalize=True)

        temp_workspace = Workspace()
        temp_octree = treemesh_2_octree(temp_workspace, treemesh)

        mesh.octree_cells = temp_octree.octree_cells
        mesh.origin = origin
        for dim in "uvw":
            attr = f"{dim}_cell_size"
            setattr(mesh, attr, np.abs(getattr(mesh, attr)))

        indices = treemesh._get_containing_cell_indexes(  # pylint: disable=W0212
            mesh.centroids
        )
        ind = np.argsort(indices)
        for child in mesh.children:
            if child.values is None or isinstance(child.values, np.ndarray):
                continue
            child.values = child.values[ind]

        return treemesh
