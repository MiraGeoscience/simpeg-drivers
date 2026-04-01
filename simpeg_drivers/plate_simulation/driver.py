# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2023-2026 Mira Geoscience Ltd.                                     '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from dask.distributed import Client
from geoapps_utils.base import Driver, get_logger
from geoapps_utils.modelling.plates import Plate
from geoapps_utils.utils.transformations import azimuth_to_unit_vector
from geoh5py.data import FloatData, ReferencedData
from geoh5py.objects import Octree, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace

from simpeg_drivers.driver import (
    InversionDriver,
    driver_class_from_name,
    validate_client,
    validate_workers,
)
from simpeg_drivers.options import BaseForwardOptions, ModelTypeEnum
from simpeg_drivers.plate_simulation.models.events import Anomaly, Erosion, Overburden
from simpeg_drivers.plate_simulation.models.series import DikeSwarm, Geology
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.utils.synthetics.meshes import get_octree_mesh
from simpeg_drivers.utils.utils import validate_out_group


logger = get_logger(__name__, propagate=False)


class PlateSimulationDriver(Driver):
    """
    Driver for simulating background + plate + overburden model.

    :param params: Parameters for plate simulation (mesh, model and
        series).
    :param client: Dask client for parallel processing.
    :param workers: List of worker addresses for Dask client.
    """

    _params_class = PlateSimulationOptions

    def __init__(
        self,
        params: PlateSimulationOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
    ):
        super().__init__(params)

        self._out_group = validate_out_group(self.params)
        self._plates: list[Plate] | None = None
        self._survey: Points | None = None
        self._mesh: Octree | None = None
        self._model: FloatData | None = None
        self._simulation_parameters: BaseForwardOptions | None = None
        self._simulation_driver: InversionDriver | None = None
        self._client: Client | bool = validate_client(client)
        self._workers: list[tuple[str]] = validate_workers(self._client, workers)

    def run(self) -> InversionDriver:
        """Create octree mesh, fill model, and simulate."""

        with fetch_active_workspace(self.params.geoh5, mode="r+"):
            self.simulation_driver.run()
            self.update_monitoring_directory(self._out_group)

        logger.info("done.")
        logger.handlers.clear()

        return self.simulation_driver

    @property
    def simulation_driver(self) -> InversionDriver:
        if self._simulation_driver is None:
            with fetch_active_workspace(self.params.geoh5, mode="r+"):
                self.simulation_parameters.mesh = self.mesh
                self.simulation_parameters.models.starting_model = self.model

                if not isinstance(
                    self.simulation_parameters.active_cells.topography_object,
                    Surface | Points,
                ):
                    raise ValueError(
                        "The topography object of the forward simulation must be a 'Surface'."
                    )

                self.simulation_parameters.out_group = None
                driver_class = driver_class_from_name(
                    self.simulation_parameters.inversion_type, forward_only=True
                )
                self._simulation_driver = driver_class(
                    self.simulation_parameters,
                    client=self._client,
                    workers=self._workers,
                )
                self._simulation_driver.out_group.parent = self._out_group

        return self._simulation_driver

    @property
    def simulation_parameters(self) -> BaseForwardOptions:
        if self._simulation_parameters is None:
            self._simulation_parameters = self.params.simulation_parameters()
            if self._simulation_parameters.physical_property == "conductivity":
                self._simulation_parameters.models.model_type = (
                    ModelTypeEnum.resistivity
                )
        return self._simulation_parameters

    @property
    def survey(self):
        if self._survey is None:
            self._survey = self.simulation_parameters.data_object

        return self._survey

    @property
    def plates(self) -> list[Plate]:
        """Generate sequence of plates."""
        if self._plates is None:
            offset = (
                self.params.model.overburden.thickness
                if self.params.model.plate.reference_surface == "overburden"
                else 0.0
            )
            center = self.params.model.plate.center(
                self.survey,
                self.topography,
                depth_offset=-1 * offset,
            )
            plate = Plate(
                self.params.model.plate.geometry.model_copy(
                    update={
                        "easting": center[0],
                        "northing": center[1],
                        "elevation": center[2],
                    }
                ),
            )
            self._plates = self.replicate(
                plate,
                self.params.model.plate.number,
                self.params.model.plate.spacing,
                self.params.model.plate.geometry.direction,
            )
        return self._plates

    @property
    def topography(self) -> Surface | Points:
        return self.simulation_parameters.active_cells.topography_object

    @property
    def mesh(self) -> Octree:
        """Returns an octree mesh built from mesh parameters."""
        if self._mesh is None:
            self._mesh = self.make_mesh()

        return self._mesh

    @property
    def model(self) -> FloatData:
        """Returns the model built from model parameters."""
        if self._model is None:
            self._model = self.make_model()

        return self._model

    def make_mesh(self) -> Octree:
        """
        Build specialized mesh for plate simulation from parameters.

        Mesh contains refinements for topography and any plates.
        """

        logger.info("making the mesh...")
        with fetch_active_workspace(self.params.geoh5, mode="r+") as geoh5:
            surfaces = [p.surface(geoh5) for p in self.plates]
            mesh = get_octree_mesh(
                opts=self.params.mesh,
                survey=self.survey,
                topography=self.simulation_parameters.active_cells.topography_object,
                plates=surfaces,
            )
        # octree_params = self.params.mesh.octree_params(
        #     self.survey,
        #     self.simulation_parameters.active_cells.topography_object,
        #     [p.surface.copy(parent=self._out_group) for p in self.plates],
        # )
        # octree_driver = OctreeDriver(octree_params)
        # mesh = octree_driver.run()
        mesh.parent = self._out_group

        return mesh

    def make_model(self) -> FloatData:
        """Create background + plate and overburden model from parameters."""

        logger.info("Building the model...")

        overburden = Overburden(
            topography=self.simulation_parameters.active_cells.topography_object,
            thickness=self.params.model.overburden.thickness,
            value=self.params.model.overburden.overburden_property,
        )

        dikes = DikeSwarm(
            [
                Anomaly(plate, self.params.model.plate.plate_property)
                for plate in self.plates
            ],
            name="plates",
        )

        erosion = Erosion(
            surface=self.simulation_parameters.active_cells.topography_object,
        )

        scenario = Geology(
            workspace=self.params.geoh5,
            mesh=self.mesh,
            background=self.params.model.background,
            history=[dikes, overburden, erosion],
        )

        geology, event_map = scenario.build()
        value_map = {k: v[0] for k, v in event_map.items()}
        physical_property_map = {k: v[1] for k, v in event_map.items()}

        physical_property = self.simulation_parameters.physical_property
        if physical_property == "conductivity":
            physical_property = "resistivity"

        model = self.mesh.add_data(
            {
                "geology": {
                    "type": "referenced",
                    "values": geology,
                    "value_map": value_map,
                }
            }
        )
        if isinstance(model, ReferencedData):
            model.add_data_map(physical_property, physical_property_map)

        starting_model_values = geology.copy()
        for k, v in physical_property_map.items():
            starting_model_values[geology == k] = v

        starting_model = self.mesh.add_data(
            {"starting_model": {"values": starting_model_values}}
        )

        if not isinstance(starting_model, FloatData):
            raise ValueError("Starting model could not be created.")

        return starting_model

    @staticmethod
    def replicate(
        plate: Plate,
        number: int,
        spacing: float,
        azimuth: float,
    ) -> list[Plate]:
        """
        Replicate a plate n times along an azimuth centered at origin.

        Plate names will be indexed.

        :param plate: models.parametric.Plate to be replicated.
        :param number: Number of plates returned.
        :param spacing: Spacing between plates.
        :param azimuth: Azimuth of the axis along with plates are replicated.
        """
        offsets = (np.arange(number) * spacing) - ((number - 1) * spacing / 2)

        plates = []
        for i in range(number):
            center = (
                np.r_[plate.params.origin]
                + azimuth_to_unit_vector(azimuth) * offsets[i]
            )
            new_plate = Plate(
                plate.params.model_copy(
                    update={
                        "easting": center[0],
                        "northing": center[1],
                        "elevation": center[2],
                    }
                )
            )

            plates.append(new_plate)

        return plates


PlateSimulationDriver.start_dask_run = InversionDriver.start_dask_run

if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateSimulationDriver.start_dask_run(file)
