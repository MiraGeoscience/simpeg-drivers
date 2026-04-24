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
from copy import deepcopy
from pathlib import Path

import numpy as np
from dask.distributed import Client
from geoapps_utils.base import Driver, get_logger
from geoapps_utils.modelling.plates import Plate
from geoapps_utils.utils.transformations import azimuth_to_unit_vector
from geoh5py.data import FloatData, ReferencedData
from geoh5py.objects import Octree, Points, Surface
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.ui_json.input_file import InputFile

from simpeg_drivers.driver import (
    InversionDriver,
    validate_client,
    validate_workers,
)
from simpeg_drivers.options import BaseForwardOptions, ModelTypeEnum
from simpeg_drivers.plate_simulation.leroi_air.driver import LeroiAirDriver
from simpeg_drivers.plate_simulation.leroi_air.options import LeroiAirOptions
from simpeg_drivers.plate_simulation.models.events import Anomaly, Erosion, Overburden
from simpeg_drivers.plate_simulation.models.series import DikeSwarm, Geology
from simpeg_drivers.plate_simulation.options import PlateSimulationOptions
from simpeg_drivers.utils.synthetics.meshes import get_octree_mesh
from simpeg_drivers.utils.utils import (
    driver_class_from_dict,
    start_dask_run,
    validate_out_group,
)


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
        self._client: Client | bool = validate_client(client)
        self._workers: list[tuple[str]] = validate_workers(self._client, workers)
        self._simulation_driver: InversionDriver | None = None
        self.simulation_parameters: BaseForwardOptions = self._initialize_forward_opts()

    def run(self) -> InversionDriver:
        """Create octree mesh, fill model, and simulate."""

        self.simulation_driver.run()
        self.simulation_parameters.update_out_group_options()
        self.update_monitoring_directory(self._out_group)

        logger.info("done.")
        logger.handlers.clear()

        return self.simulation_driver

    @property
    def simulation_driver(self) -> InversionDriver:
        if self._simulation_driver is None:
            if self.params.use_leroi:
                _ = self.plates  # Saves MaxwellPlate(s) when no octree/model
                self._simulation_driver = self._get_leroi_driver()
            else:
                self._simulation_driver = self._get_simpeg_driver()

        return self._simulation_driver

    @property
    def survey(self):
        return self.simulation_parameters.data_object

    @property
    def topography(self) -> Surface | Points:
        return self.simulation_parameters.active_cells.topography_object

    @property
    def plates(self) -> list[Plate]:
        """Generate sequence of plates."""
        if self._plates is None:
            center = self.params.model.plate_options.center(
                self.survey,
                self.topography,
            )
            plate = Plate(
                self.params.model.plate_options.geometry.model_copy(
                    update={
                        "easting": center[0],
                        "northing": center[1],
                        "elevation": center[2],
                    }
                ),
            )
            self._plates = self.replicate(
                plate,
                self.params.model.plate_options.number,
                self.params.model.plate_options.spacing,
                self.params.model.plate_options.geometry.direction,
            )
            for plate in self._plates:
                plate.to_maxwell_plate(self.params.geoh5, parent=self._out_group)

        return self._plates

    def make_mesh(self) -> Octree:
        """
        Build specialized mesh for plate simulation from parameters.

        Mesh contains refinements for topography and any plates.
        """

        logger.info("making the mesh...")
        surfaces = [p.surface(self.params.geoh5) for p in self.plates]
        self._mesh = get_octree_mesh(
            opts=self.params.mesh,
            survey=self.survey,
            topography=self.simulation_parameters.active_cells.topography_object,
            plates=surfaces,
            name="Octree",
        )
        self._mesh.parent = self._out_group

        return self._mesh

    def make_model(self) -> FloatData:
        """Create background + plate and overburden model from parameters."""

        logger.info("Building the model...")

        overburden = Overburden(
            topography=self.simulation_parameters.active_cells.topography_object,
            thickness=self.params.model.overburden_options.thickness,
            value=self.params.model.overburden_options.overburden_property,
        )

        dikes = DikeSwarm(
            [
                Anomaly(plate, self.params.model.plate_options.plate_property)
                for plate in self.plates
            ],
            name="plates",
        )

        erosion = Erosion(
            surface=self.simulation_parameters.active_cells.topography_object,
        )

        scenario = Geology(
            workspace=self.params.geoh5,
            mesh=self.simulation_parameters.mesh,
            background=self.params.model.background,
            history=[dikes, overburden, erosion],
        )

        geology, event_map = scenario.build()
        value_map = {k: v[0] for k, v in event_map.items()}
        physical_property_map = {k: v[1] for k, v in event_map.items()}

        physical_property = self.simulation_parameters.physical_property
        if physical_property == "conductivity":
            physical_property = "resistivity"

        model = self._mesh.add_data(
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

        starting_model = self.simulation_parameters.mesh.add_data(
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

    @classmethod
    def start_dask_run(
        cls, json_path: Path, n_workers: int | None = None, n_threads: int | None = None
    ):
        """
        Runs the plate simulation application with Dask optimization.

        :param json_path: Path to input file (.ui.json) for the application.
        :param n_workers: Number of workers to use.
        :param n_threads: Number of threads to use.
        """
        start_dask_run(cls, json_path, n_workers=n_workers, n_threads=n_threads)

    def _get_simpeg_driver(self):

        if not isinstance(
            self.simulation_parameters.active_cells.topography_object,
            Surface | Points,
        ):
            raise ValueError(
                "The topography object of the forward simulation must be a 'Surface'."
            )

        driver_class = driver_class_from_dict(self.simulation_parameters.__dict__)
        self.simulation_parameters.mesh = self.make_mesh()
        self.simulation_parameters.models.starting_model = self.make_model()
        self._simulation_driver = driver_class(
            self.simulation_parameters,
            client=self._client,
            workers=self._workers,
        )

        return self._simulation_driver

    def _get_leroi_driver(self):
        leroi_opts = LeroiAirOptions.from_plate_simulation_options(
            self.params.model, self.simulation_parameters
        )
        driver = LeroiAirDriver(leroi_opts)
        return driver

    def _collect_simulation_opts(self) -> BaseForwardOptions:
        """Collect template simulation options."""

        simulation_options = deepcopy(self.params.simulation.options)
        simulation_options["geoh5"] = self.params.geoh5

        # TODO replace InputFile.data with UIJson.to_params
        input_file = InputFile(ui_json=simulation_options, validate=False)
        driver = driver_class_from_dict(input_file.data)

        return driver._params_class.build(input_file.data)  # pylint: disable=protected-access

    def _initialize_forward_opts(self) -> BaseForwardOptions:
        """Initialize the forward simulation options with mesh and model."""

        opts = self._collect_simulation_opts()

        update = {}
        models_update = {}
        if opts.physical_property == "conductivity":
            # TODO: validate this logic
            models_update["model_type"] = ModelTypeEnum.resistivity
        if not self.params.use_leroi:
            update["mesh"] = None
            models_update["starting_model"] = None
        update["models"] = opts.models.model_copy(update=models_update)

        out_group = validate_out_group(opts)
        out_group = out_group.copy(
            parent=self.out_group,
            copy_children=False,
            copy_relatives=False,
        )
        update["out_group"] = out_group
        forward_opts = opts.model_copy(update=update)
        forward_opts.update_out_group_options()

        return forward_opts


if __name__ == "__main__":
    file = Path(sys.argv[1])
    PlateSimulationDriver.start_dask_run(file)
