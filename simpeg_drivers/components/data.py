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

from copy import deepcopy
from re import findall
from typing import TYPE_CHECKING, Any

import numpy as np
from discretize import TensorMesh, TreeMesh
from geoh5py.objects import PotentialElectrode
from scipy.sparse import csgraph, csr_matrix
from scipy.spatial import cKDTree
from simpeg import maps
from simpeg.electromagnetics.static.utils.static_utils import geometric_factor
from simpeg.simulation import BaseSimulation

from simpeg_drivers.utils.utils import create_nested_mesh, drape_2_tensor

from .factories import (
    EntityFactory,
    SaveDataGeoh5Factory,
    SimulationFactory,
    SurveyFactory,
)
from .locations import InversionLocations


if TYPE_CHECKING:
    from geoh5py.workspace import Workspace

    from simpeg_drivers.components.meshes import InversionMesh
    from simpeg_drivers.options import InversionBaseOptions


class InversionData(InversionLocations):
    """
    Retrieve and store data from the workspace and apply normalizations.

    Parameters
    ---------

    locations :
        Data locations.
    mask :
        Mask accumulated by windowing and downsampling operations and applied
        to locations and data on initialization.
    n_blocks :
        Number of blocks if vector.
    components :
        Component names.
    observed :
        Components and associated observed geophysical data.
    uncertainties :
        Components and associated data uncertainties.
    normalizations :
        Data normalizations.

    Methods
    -------

    survey(local_index=None) :
        Generates SimPEG survey object.
    simulation(mesh, active_cells, local_index=None, tile_id=None) :
        Generates SimPEG simulation object.

    """

    def __init__(self, workspace: Workspace, params: InversionBaseOptions):
        """
        :param: workspace: :obj`geoh5py.workspace.Workspace` workspace object containing location based data.
        :param: params: Options object containing location based data parameters.
        """
        super().__init__(workspace, params)
        self.locations: np.ndarray | None = None
        self.mask: np.ndarray | None = None
        self.n_blocks: int | None = None

        self._observed: dict[str, np.ndarray] | None = None
        self._uncertainties: dict[str, np.ndarray] | None = None

        self.entity = None
        self.data_entity = None
        self._observed_data_types = {}
        self._survey = None

        self._initialize()

    def _initialize(self) -> None:
        """Extract data from the workspace using params data."""
        self.n_blocks = 3 if self.params.inversion_type == "magnetic vector" else 1
        self.components = self.params.active_components

        self.has_tensor = InversionData.check_tensor(self.params.components)
        self.locations = super().get_locations(self.params.data_object)

        if "2d" in self.params.inversion_type:
            self.mask = (
                self.params.line_selection.line_object.values
                == self.params.line_selection.line_id
            )
        else:
            self.mask = np.ones(len(self.locations), dtype=bool)

        self.normalizations: dict[str, Any] = self.get_normalizations()

        self.entity = self.write_entity()

        self.save_data()
        self.locations = super().get_locations(self.entity)

    @property
    def observed(self):
        """
        Return observed data filtered and normalized.
        """
        if self._observed is None:
            filtered = self.filter(self.params.data, mask=self.mask)
            self._observed = self.normalize(filtered)

        return self._observed

    @property
    def uncertainties(self):
        """
        Return uncertainties filtered and normalized.
        """
        if self._uncertainties is None and hasattr(self.params, "uncertainties"):
            filtered = self.filter(self.params.uncertainties, mask=self.mask)
            self._uncertainties = self.normalize(filtered, absolute=True)

        return self._uncertainties

    @property
    def parts(self):
        """
        Return parts indices from the entity.
        """
        if isinstance(self.entity, PotentialElectrode):
            edge_array = csr_matrix(
                (
                    np.ones(self.entity.n_cells * 2),
                    (
                        np.kron(self.entity.cells[:, 0], [1, 1]),
                        self.entity.cells.flatten(),
                    ),
                ),
                shape=(self.entity.n_vertices, self.entity.n_vertices),
            )

            connections = csgraph.connected_components(edge_array)[1]
            return connections[self.entity.cells[:, 0]]

        return getattr(self.entity, "parts", None)

    def drape_locations(self, locations: np.ndarray) -> np.ndarray:
        """
        Return pseudo locations along line in distance, depth.

        The horizontal distance is referenced to first node of the core mesh.

        """
        local_tensor = drape_2_tensor(self.params.mesh)

        # Interpolate distance assuming always inside the mesh trace
        tree = cKDTree(self.params.mesh.prisms[:, :2])
        rad, ind = tree.query(locations[:, :2], k=2)
        distance_interp = 0.0
        for ii in range(2):
            distance_interp += local_tensor.cell_centers_x[ind[:, ii]] / (
                rad[:, ii] + 1e-8
            )

        distance_interp /= ((rad + 1e-8) ** -1.0).sum(axis=1)

        return np.c_[distance_interp, locations[:, 2:]]

    def get_data(self) -> tuple[list, dict, dict]:
        """
        Get all data and uncertainty components and possibly set infinite uncertainties.

        :return: components: list of data components sorted in the
            order of self.observed.keys().
        :return: data: Dictionary of components and associated data
        :return: uncertainties: Dictionary of components and
            associated uncertainties.
        """

        data = {}
        uncertainties = {}

        for comp in self.params.components:
            data.update({comp: self.params.data(comp)})
            uncertainties.update({comp: self.params.uncertainty(comp)})

        return list(data.keys()), data, uncertainties

    def write_entity(self):
        """Write out the survey to geoh5"""
        entity_factory = EntityFactory(self.params)
        entity = entity_factory.build(self)

        return entity

    def save_data(self):
        """Write out the data to geoh5"""
        has_channels = self.params.inversion_type in [
            "magnetotellurics",
            "tipper",
            "tdem",
            "fdem",
            "fdem 1d",
            "tdem 1d",
        ]

        # Pre-allocate dictionaries
        data_types = {c: {} for c in self.observed.keys()}
        data_dict = data_types.copy()
        uncert_dict = data_types.copy()

        for component, channels in self.observed.items():
            # Forward only
            if channels is None:
                continue

            # Non-EM methods
            if not has_channels:
                channels = {None: channels}

            for ind, (channel, values) in enumerate(channels.items()):
                suffix = f"_{component}"
                if has_channels:
                    suffix += f"_[{ind}]"

                normalized_data = values / self.normalizations[channel][component]
                data_entity = self.entity.add_data(
                    {"Observed" + suffix: {"values": normalized_data}}
                )
                uncerts = np.abs(
                    self.uncertainties[component][channel].flatten()
                    / self.normalizations[channel][component]
                )
                uncerts[np.isinf(uncerts)] = np.nan
                uncert_entity = self.entity.add_data(
                    {"Uncertainties" + suffix: {"values": uncerts}}
                )

                if has_channels:
                    data_dict[component] = self.entity.add_data_to_group(
                        data_entity, f"Observed_{component}"
                    )
                    uncert_dict[component] = self.entity.add_data_to_group(
                        uncert_entity, f"Uncertainties_{component}"
                    )
                else:
                    data_dict[component] = data_entity
                    uncert_dict[component] = uncert_entity

                data_types[component][channel] = data_entity.entity_type

        self._observed_data_types = data_types
        self.update_params(data_dict, uncert_dict)

    def normalize(
        self, data: dict[str, np.ndarray], absolute=False
    ) -> dict[str, np.ndarray]:
        """
        Apply data type specific normalizations to data.

        Calling normalize will apply the normalization to the data AND append
        to the normalizations attribute list the value applied to the data.

        :param: data: Components and associated geophysical data.

        :return: d: Normalized data.
        """
        d = deepcopy(data)
        for chan in getattr(self.params.data_object, "channels", [None]):
            for comp in self.params.active_components:
                if isinstance(d[comp], dict):
                    if d[comp][chan] is not None:
                        d[comp][chan] *= self.normalizations[chan][comp]
                        if absolute:
                            d[comp][chan] = np.abs(d[comp][chan])
                elif d[comp] is not None:
                    d[comp] *= self.normalizations[chan][comp]
                    if absolute:
                        d[comp] = np.abs(d[comp])

        return d

    def get_normalizations(self):
        """Create normalizations dictionary."""
        normalizations = {}
        for chan in getattr(self.params.data_object, "channels", [None]):
            normalizations[chan] = {}
            for comp in self.params.active_components:
                normalizations[chan][comp] = np.ones(self.mask.sum())
                if comp in ["potential", "chargeability"]:
                    normalizations[chan][comp] = 1
                if comp in ["gz", "bz", "gxz", "gyz", "bxz", "byz"]:
                    normalizations[chan][comp] = -1 * np.ones(self.mask.sum())
                elif self.params.inversion_type in ["magnetotellurics"]:
                    normalizations[chan][comp] = -1 * np.ones(self.mask.sum())
                elif self.params.inversion_type in ["tipper"]:
                    if "imag" in comp:
                        normalizations[chan][comp] = -1 * np.ones(self.mask.sum())
                elif "fdem" == self.params.inversion_type:  # Assume always ppm data
                    mu0 = 4 * np.pi * 1e-7
                    offsets = self.params.tx_offsets
                    offsets = {
                        k: v * np.ones(len(self.locations)) for k, v in offsets.items()
                    }
                    normalizations[chan][comp] = (
                        mu0 * (-1 / offsets[chan] ** 3 / (4 * np.pi)) / 1e6
                    )
                elif (
                    "tdem" in self.params.inversion_type
                    and "dB/dt" in self.params.data_units
                ):
                    if comp in ["x", "y", "z"]:
                        normalizations[chan][comp] = -1
                    normalizations[chan][comp] *= np.ones(self.mask.sum())

        return normalizations

    def create_survey(
        self,
        local_index: np.ndarray | None = None,
        channel=None,
    ):
        """
        Generates SimPEG survey object.

        :param: local_index (Optional): Indices of the data belonging to a
            particular tile in case of a tiled inversion.

        :return: survey: SimPEG Survey class that covers all data or optionally
            the portion of the data indexed by the local_index argument.
        :return: local_index: receiver indices belonging to a particular tile.
        """

        survey_factory = SurveyFactory(self.params)
        survey, local_index, ordering = survey_factory.build(
            data=self,
            local_index=local_index,
            channel=channel,
        )

        if "direct current" in self.params.inversion_type:
            survey.apparent_resistivity = 1 / (
                geometric_factor(survey)[np.argsort(np.hstack(local_index))] + 1e-10
            )

        return survey, local_index, ordering

    def simulation(
        self,
        inversion_mesh: InversionMesh,
        local_mesh: TreeMesh | TensorMesh | None,
        active_cells: np.ndarray,
        survey,
        tile_id: int | None = None,
        padding_cells: int = 6,
    ) -> tuple[BaseSimulation, maps.IdentityMap]:
        """
        Generates SimPEG simulation object.

        :param: mesh: inversion mesh.
        :param: active_cells: Mask that reduces model to active (earth) cells.
        :param: survey: SimPEG survey object.
        :param: tile_id (Optional): Id associated with the tile covered by
            the survey in case of a tiled inversion.

        :return: sim: SimPEG simulation object for full data or optionally
            the portion of the data indexed by the local_index argument.
        :return: map: If local_index and tile_id is provided, the returned
            map will maps from local to global data.  If no local_index or
            tile_id is provided map will simply be an identity map with no
            effect of the data.
        """
        simulation_factory = SimulationFactory(self.params)

        if tile_id is None or "2d" in self.params.inversion_type:
            mapping = maps.IdentityMap(nP=int(self.n_blocks * active_cells.sum()))
            simulation = simulation_factory.build(
                survey=survey,
                global_mesh=inversion_mesh.mesh,
                active_cells=active_cells,
                mapping=mapping,
            )
        elif "1d" in self.params.inversion_type:
            slice_ind = np.arange(
                tile_id, inversion_mesh.mesh.n_cells, inversion_mesh.mesh.shape_cells[0]
            )[::-1]
            mapping = maps.Projection(inversion_mesh.mesh.n_cells, slice_ind)
            simulation = simulation_factory.build(
                survey=survey,
                receivers=self.entity,
                global_mesh=inversion_mesh.mesh,
                local_mesh=inversion_mesh.layers_mesh,
                active_cells=active_cells,
                mapping=mapping,
                tile_id=tile_id,
            )
        else:
            if local_mesh is None:
                local_mesh = create_nested_mesh(
                    survey,
                    inversion_mesh.mesh,
                    minimum_level=3,
                    padding_cells=padding_cells,
                )
            mapping = maps.TileMap(
                inversion_mesh.mesh,
                active_cells,
                local_mesh,
                enforce_active=True,
                components=self.n_blocks,
            )
            simulation = simulation_factory.build(
                survey=survey,
                receivers=self.entity,
                global_mesh=inversion_mesh.mesh,
                local_mesh=local_mesh,
                active_cells=mapping.local_active,
                mapping=mapping,
                tile_id=tile_id,
            )

        return simulation, mapping

    def simulate(self, model, inverse_problem, sorting, ordering):
        """Simulate fields for a particular model."""
        dpred = inverse_problem.get_dpred(
            model, compute_J=False if self.params.forward_only else True
        )
        if self.params.forward_only:
            save_directive = SaveDataGeoh5Factory(self.params).build(
                inversion_object=self,
                sorting=np.argsort(np.hstack(sorting)),
                ordering=ordering,
            )
            save_directive.write(0, dpred)

        inverse_problem.dpred = dpred

    @property
    def observed_data_types(self):
        """
        Stored data types
        """
        return self._observed_data_types

    @staticmethod
    def check_tensor(channels):
        tensor_components = "|".join(
            ["xx", "xy", "xz", "yx", "zx", "yy", "zz", "zy", "yz"]
        )

        for channel in channels:
            if any(findall(tensor_components, channel)):
                return True

        return False

    def update_params(self, data_dict, uncert_dict):
        """
        Update pointers to newly created object and data.
        """
        self.params.data_object = self.entity
        for comp in self.params.components:
            if getattr(self.params, "_".join([comp, "channel"]), None) is None:
                continue

            setattr(self.params, f"{comp}_channel", data_dict[comp])
            setattr(self.params, f"{comp}_uncertainty", uncert_dict[comp])

        if getattr(self.params, "line_selection", None) is not None:
            new_line = self.params.line_selection.line_object.copy(
                parent=self.entity,
                values=self.params.line_selection.line_object.values[self.mask],
            )
            self.params.line_selection.line_object = new_line

    @property
    def survey(self):
        if self._survey is None:
            self._survey, _, _ = self.create_survey()

        return self._survey

    @property
    def n_data(self):
        n_data = 0
        for comp in self.params.active_components:
            if isinstance(self.observed[comp], dict):
                for channel in self.observed[comp]:
                    n_data += len(self.observed[comp][channel])
            else:
                n_data += len(self.observed[comp])

        return n_data
