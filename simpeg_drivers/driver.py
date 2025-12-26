# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# flake8: noqa

from __future__ import annotations

import cProfile
import pstats

import multiprocessing
import contextlib
from copy import deepcopy
import sys
from datetime import datetime, timedelta
import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path
from time import time

from typing_extensions import Self

import numpy as np
from dask import config as dconf

from dask.distributed import get_client, Client, LocalCluster, performance_report

from geoapps_utils.base import Driver, Options
from geoapps_utils.run import load_ui_json_as_dict
from geoapps_utils.utils.importing import GeoAppsError
from geoapps_utils.param_sweeps.driver import SweepParams

from geoh5py.groups import SimPEGGroup
from geoh5py.objects import FEMSurvey
from geoh5py.shared.utils import fetch_active_workspace
from geoh5py.shared.exceptions import Geoh5FileClosedError
from geoh5py.ui_json import InputFile

from simpeg import (
    dask,
    directives,
    inverse_problem,
    inversion,
    maps,
    objective_function,
    optimization,
    simulation,
)
from simpeg.electromagnetics.frequency_domain.simulation_1d import Simulation1DLayered

from simpeg.regularization import (
    BaseRegularization,
    RegularizationMesh,
    Sparse,
    SparseSmoothness,
)

from simpeg_drivers import DRIVER_MAP, __version__
from simpeg_drivers.components import (
    InversionData,
    InversionMesh,
    InversionModelCollection,
    InversionTopography,
    InversionWindow,
)
from simpeg_drivers.components.factories import (
    DirectivesFactory,
    MisfitFactory,
    SimulationFactory,
)
from simpeg_drivers.options import (
    BaseForwardOptions,
    BaseInversionOptions,
)
from simpeg_drivers.joint.options import BaseJointOptions
from simpeg_drivers.utils.nested import tile_locations
from simpeg_drivers.utils.regularization import cell_neighbors, set_rotated_operators

mlogger = logging.getLogger("distributed")
mlogger.setLevel(logging.WARNING)


class BaseDriver(Driver):
    """
    Base class for drivers handling the parallel setup.
    """

    def __init__(
        self,
        params: Options,
        client: Client | bool | None = None,
        workers: list[str] | None = None,
    ):
        super().__init__(params)
        self._client: Client | bool = self.validate_client(client)

        if getattr(self.params, "store_sensitivities", None) == "disk" and self.client:
            raise GeoAppsError(
                "Disk storage of sensitivities is not compatible with distributed processing."
            )

        self._workers: list[tuple[str]] | None = self.validate_workers(workers)

    @property
    def client(self) -> Client | bool | None:
        """
        Dask client or False if not using Dask.distributed.
        """
        return self._client

    @property
    def workers(self) -> list[tuple[str]]:
        """List of workers stored as a list of tuples."""
        return self._workers

    def validate_client(self, client: Client | bool | None) -> Client | bool:
        """
        Validate or create a Dask client.
        """
        if client is None:
            try:
                client = get_client()
            except ValueError:
                client = False
        return client

    def validate_workers(self, workers: list[tuple[str]] | None) -> list[tuple[str]]:
        """
        Validate the list of workers.
        """
        if self.client:
            available_workers = [(worker,) for worker in self.client.nthreads()]
        else:
            return []

        if workers is None:
            return available_workers

        if not isinstance(workers, list) or not all(
            isinstance(w, tuple) for w in workers
        ):
            raise TypeError("Workers must be a list of tuple[str].")

        invalid_workers = [w for w in workers if w not in available_workers]
        if invalid_workers:
            raise ValueError(
                f"The following workers are not available: {invalid_workers}. "
                f"Available workers are: {available_workers}."
            )

        return workers


class InversionDriver(BaseDriver):
    _params_class = BaseForwardOptions | BaseInversionOptions
    _inversion_type: str | None = None

    def __init__(
        self,
        params: BaseForwardOptions | BaseInversionOptions,
        client: Client | bool | None = None,
        workers: list[tuple[str]] | None = None,
        logger: logging.Logger | None | bool = None,
    ):
        super().__init__(params, client=client, workers=workers)

        self.inversion_type = self.params.inversion_type
        self.out_group = self.validate_out_group(self.params.out_group)
        self._data_misfit: objective_function.ComboObjectiveFunction | None = None
        self._directives: list[directives.InversionDirective] | None = None
        self._inverse_problem: inverse_problem.BaseInvProblem | None = None
        self._inversion: inversion.BaseInversion | None = None
        self._inversion_data: InversionData | None = None
        self._inversion_mesh: InversionMesh | None = None
        self._inversion_topography: InversionTopography | None = None
        self.logger: InversionLogger | None = logger
        self._mapping: list[maps.IdentityMap] | None = None
        self._models: InversionModelCollection | None = None
        self._n_values: int | None = None
        self._optimization: optimization.ProjectedGNCG | None = None
        self._regularization: None = None
        self._simulation: simulation.BaseSimulation | None = None

        self._ordering: list[np.ndarray] | None = None
        self._mappings: list[maps.IdentityMap] | None = None
        self._window = None

    def split_list(self, tiles: list[np.ndarray]) -> list[np.ndarray]:
        """
        Number of splits for the data misfit to be distributed evenly among workers.
        """
        if len(self.workers) == 0:
            return [[tile] for tile in tiles]

        n_tiles = len(tiles)

        n_channels = 1
        if isinstance(self.params.data_object, FEMSurvey) and not isinstance(
            self.simulation, Simulation1DLayered
        ):
            n_channels = len(self.params.data_object.channels)

        split_list = [1] * n_tiles

        count = 0
        while (np.sum(split_list) * n_channels) % len(self.workers) != 0:
            split_list[count % n_tiles] += 1
            count += 1

        if self.logger:
            self.logger.write(
                f"Number of misfits: {np.sum(split_list)} distributed over {len(self.workers)} workers.\n"
            )

        flat_tile_list = []
        for tile, split in zip(tiles, split_list):
            flat_tile_list.append(np.array_split(tile, split))
        return flat_tile_list

    @property
    def data_misfit(self):
        """The Simpeg.data_misfit class"""
        if getattr(self, "_data_misfit", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                # Tile locations
                tiles = self.get_tiles()

                if self.logger:
                    self.logger.write(f"Setting up {len(tiles)} tile(s) . . .\n")

                self._data_misfit = MisfitFactory(
                    self.params, self.client, self.simulation, self.workers
                ).build(
                    self.split_list(tiles),
                )

        return self._data_misfit

    @property
    def directives(self):
        if getattr(self, "_directives", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._directives = DirectivesFactory(self)
        return self._directives

    @property
    def inverse_problem(self):
        if getattr(self, "_inverse_problem", None) is None:
            self._inverse_problem = inverse_problem.BaseInvProblem(
                self.data_misfit,
                self.regularization,
                self.optimization,
            )

            if (
                not self.params.forward_only
                and self.params.cooling_schedule.initial_beta
            ):
                self._inverse_problem.beta = self.params.cooling_schedule.initial_beta

        return self._inverse_problem

    @property
    def inversion(self):
        if getattr(self, "_inversion", None) is None:
            self._inversion = inversion.BaseInversion(
                self.inverse_problem, directiveList=self.directives.directive_list
            )
        return self._inversion

    @property
    def inversion_data(self) -> InversionData:
        """Inversion data"""
        if getattr(self, "_inversion_data", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._inversion_data = InversionData(self.workspace, self.params)

        return self._inversion_data

    @property
    def inversion_mesh(self) -> InversionMesh:
        """Inversion mesh"""
        if getattr(self, "_inversion_mesh", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._inversion_mesh = InversionMesh(self.workspace, self.params)
        return self._inversion_mesh

    @property
    def inversion_topography(self):
        """Inversion topography"""
        if getattr(self, "_inversion_topography", None) is None:
            self._inversion_topography = InversionTopography(
                self.workspace, self.params
            )
        return self._inversion_topography

    @property
    def inversion_type(self) -> str | None:
        """Inversion type"""
        return self._inversion_type

    @inversion_type.setter
    def inversion_type(self, value):
        if value not in DRIVER_MAP:
            raise ValueError(f"Invalid inversion type: {value}")
        self._inversion_type = value

    @property
    def logger(self) -> InversionLogger | None:
        """
        Inversion logger
        """
        return self._logger

    @logger.setter
    def logger(self, value: InversionLogger | None | bool):
        if value is True or value is None:
            self._logger = InversionLogger("SimPEG.log", self)
        elif value is False:
            self._logger = None
        elif isinstance(value, logging.Logger):
            self._logger = value
        else:
            raise TypeError(
                "Logger must be a InversionLogger instance, None, True or False."
            )

    @property
    def models(self):
        """Inversion models"""
        if getattr(self, "_models", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                self._models = InversionModelCollection(self)

        return self._models

    @property
    def n_blocks(self):
        """
        Number of model components in the inversion.
        """
        return 3 if self.params.inversion_type == "magnetic vector" else 1

    @property
    def n_values(self):
        """Number of values in the model"""
        if self._n_values is None:
            self._n_values = self.models.n_active

        return self._n_values

    @property
    def optimization(self):
        if getattr(self, "_optimization", None) is None:
            if self.params.forward_only:
                return optimization.ProjectedGNCG()

            self._optimization = optimization.ProjectedGNCG(
                maxIter=self.params.optimization.max_global_iterations,
                lower=self.models.lower_bound,
                upper=self.models.upper_bound,
                maxIterLS=self.params.optimization.max_line_search_iterations,
                maxIterCG=self.params.optimization.max_cg_iterations,
                tolCG=self.params.optimization.tol_cg,
                stepOffBoundsFact=1e-8,
                LSshorten=0.25,
            )
        return self._optimization

    @property
    def ordering(self):
        """List of ordering of the data."""
        return self.inversion_data.survey.ordering

    @property
    def out_group(self) -> SimPEGGroup:
        """
        Returns the output group for the simulation.
        """
        return self._out_group

    @out_group.setter
    def out_group(self, value: SimPEGGroup):
        if not isinstance(value, SimPEGGroup):
            raise TypeError("Output group must be a SimPEGGroup.")

        self.params.out_group = value
        self.params.update_out_group_options()
        self._out_group = value

    def validate_out_group(self, out_group: SimPEGGroup | None) -> SimPEGGroup:
        """
        Validate or create a SimPEGGroup to store results.

        :param out_group: Output group from selection.
        """
        if isinstance(out_group, SimPEGGroup):
            return out_group

        with fetch_active_workspace(self.workspace, mode="r+"):
            out_group = SimPEGGroup.create(self.workspace, name=self.params.title)

        return out_group

    @property
    def params(self) -> BaseForwardOptions | BaseInversionOptions:
        """Application parameters."""
        return self._params

    @params.setter
    def params(
        self,
        val: BaseForwardOptions | BaseInversionOptions | SweepParams,
    ):
        if not isinstance(
            val,
            (
                BaseForwardOptions,
                BaseInversionOptions,
                SweepParams,
                BaseJointOptions,
            ),
        ):
            raise TypeError(
                "Parameters must be of type 'BaseInversionOptions', 'BaseForwardOptions' or 'SweepParams'."
            )
        self._params = val

    @property
    def regularization(self):
        if getattr(self, "_regularization", None) is None:
            with fetch_active_workspace(self.workspace, mode="r"):
                if self.logger:
                    self.logger.write("Creating the regularization functions...\n")

                self._regularization = self.get_regularization()

        return self._regularization

    @regularization.setter
    def regularization(self, regularization: objective_function.ComboObjectiveFunction):
        if not isinstance(regularization, objective_function.ComboObjectiveFunction):
            raise TypeError(
                f"Regularization must be a ComboObjectiveFunction, not {type(regularization)}."
            )
        self._regularization = regularization

    @property
    def simulation(self):
        """
        The simulation object used in the inversion.
        """
        if getattr(self, "_simulation", None) is None:
            simulation_factory = SimulationFactory(self.params)
            self._simulation = simulation_factory.build(
                mesh=self.inversion_mesh.mesh,
                models=self.models,
                survey=self.inversion_data.survey,
            )

            if not hasattr(self._simulation, "active_cells"):
                self._simulation.active_cells = self.models.active_cells

        return self._simulation

    @property
    def window(self):
        """Inversion window"""
        if getattr(self, "_window", None) is None:
            self._window = InversionWindow(self.workspace, self.params)
        return self._window

    def run(self):
        """Run inversion from params"""
        if self.logger:
            sys.stdout = self.logger
            self.logger.start()

        self.configure_dask()

        with fetch_active_workspace(self.workspace, mode="r+"):
            simpeg_inversion = self.inversion

            if Path(self.params.input_file.path_name).is_file():
                self.out_group.add_file(self.params.input_file.path_name)

        predicted = None
        try:
            if self.params.forward_only:
                if self.logger:
                    self.logger.write("Running the forward simulation ...\n")
                predicted = simpeg_inversion.invProb.get_dpred(
                    self.models.starting_model, None
                )
            else:
                # Run the inversion
                if self.logger:
                    self.start_inversion_message()
                simpeg_inversion.run(self.models.starting_model)

        except np.core._exceptions._ArrayMemoryError as error:  # pylint: disable=protected-access
            raise GeoAppsError(
                "Memory Error: Sensitivities too large for system. \n"
                "Try reducing the number of data, reducing the number of cells in the mesh\n"
                "or increase the number of tiles."
            ) from error

        if self.logger:
            self.logger.end()
            sys.stdout = self.logger.terminal

        if self.params.forward_only:
            self.directives.save_iteration_data_directive.write(0, predicted)

            if (
                isinstance(
                    self.directives.save_iteration_data_directive,
                    directives.SaveDataGeoH5,
                )
                and len(self.directives.save_iteration_data_directive.channels) > 1
            ):
                directives.SavePropertyGroup(
                    self.inversion_data.entity,
                    channels=self.directives.save_iteration_data_directive.channels,
                    components=self.directives.save_iteration_data_directive.components,
                ).write(0)

        with fetch_active_workspace(self.workspace, mode="r+"):
            for directive in self.directives.save_directives:
                if isinstance(directive, directives.SaveLogFilesGeoH5):
                    directive.write(1)

    def count_data(self):
        """
        Returns the finite (not nan) and total data counts for drivers.

        Iterates and accumulates over collection of drivers if joint inversion.
        """
        drivers = [self]
        if hasattr(self, "drivers"):
            drivers = self.drivers

        finite_data_count, total_data_count = 0, 0
        for driver in drivers:
            finite_data_count += driver.inversion_data.n_data(finite_only=True)
            total_data_count += driver.inversion_data.n_data(finite_only=False)

        return finite_data_count, total_data_count

    def start_inversion_message(self):
        # SimPEG reports half phi_d, so we scale to match
        has_chi_start = self.params.irls.starting_chi_factor is not None
        chi_start = (
            self.params.irls.starting_chi_factor
            if has_chi_start
            else self.params.cooling_schedule.chi_factor
        )

        finite_data_count, total_data_count = self.count_data()
        rescale = finite_data_count / total_data_count
        rescaled_chi_factor = self.params.cooling_schedule.chi_factor * rescale
        rescaled_starting_chi_factor = chi_start * rescale
        self.logger.write(
            f"Target Misfit: {rescaled_chi_factor * total_data_count:.2e} ({finite_data_count} data "
            f"with chifact = {self.params.cooling_schedule.chi_factor})\n"
        )
        self.logger.write(
            f"IRLS Start Misfit: {rescaled_starting_chi_factor * total_data_count:.2e} ({finite_data_count} data "
            f"with chifact = {self.params.irls.starting_chi_factor})\n"
        )

    @property
    def mapping(self) -> list[maps.IdentityMap] | None:
        """Model mapping for the inversion."""
        if self._mapping is None:
            self.mapping = maps.IdentityMap(nP=self.n_values)

        return self._mapping

    @mapping.setter
    def mapping(self, value: maps.IdentityMap | list[maps.IdentityMap]):
        if not isinstance(value, list):
            value = [value]

        if not all(
            isinstance(val, maps.IdentityMap) and val.shape[0] == self.n_values
            for val in value
        ):
            raise TypeError(
                "'mapping' must be an instance of maps.IdentityMap with shape (n_values, *). "
                f"Provided {value}"
            )

        self._mapping = value

    def get_regularization(self):
        if self.params.forward_only:
            return BaseRegularization(mesh=self.inversion_mesh.mesh)

        reg_funcs = []
        is_rotated = self.params.models.gradient_rotation is not None
        neighbors = None
        backward_mesh = None
        forward_mesh = None
        for mapping in self.mapping:
            reg_func = Sparse(
                forward_mesh or self.inversion_mesh.mesh,
                active_cells=self.models.active_cells if forward_mesh is None else None,
                mapping=mapping,
                reference_model=self.models.reference_model,
            )

            if is_rotated and neighbors is None:
                backward_mesh = RegularizationMesh(
                    self.inversion_mesh.mesh, active_cells=self.models.active_cells
                )
                neighbors = cell_neighbors(reg_func.regularization_mesh.mesh)

            # Adjustment for 2D versus 3D problems
            components = (
                "sxz"
                if (
                    "2d" in self.params.inversion_type
                    or "1d" in self.params.inversion_type
                )
                else "sxyz"
            )
            weight_names = ["alpha_s"] + [f"length_scale_{k}" for k in components[1:]]
            functions = []
            for comp, weight_name, fun in zip(
                components, weight_names, reg_func.objfcts
            ):
                if getattr(self.models, weight_name) is None:
                    setattr(reg_func, weight_name, 0.0)
                    functions.append(fun)
                    continue

                weight = mapping * getattr(self.models, weight_name)
                norm = mapping * getattr(self.models, f"{comp}_norm")

                if not isinstance(fun, SparseSmoothness):
                    fun.set_weights(**{comp: weight})
                    fun.norm = norm
                    functions.append(fun)
                    continue

                if is_rotated:
                    if forward_mesh is None:
                        fun = set_rotated_operators(
                            fun,
                            neighbors,
                            comp,
                            self.models.gradient_dip,
                            self.models.gradient_direction,
                        )

                average_op = getattr(
                    reg_func.regularization_mesh,
                    f"aveCC2F{fun.orientation}",
                )
                fun.set_weights(**{comp: average_op @ weight})
                fun.norm = np.round(average_op @ norm, decimals=3)
                functions.append(fun)

                if is_rotated:
                    fun.gradient_type = "components"
                    backward_fun = deepcopy(fun)
                    setattr(backward_fun, "_regularization_mesh", backward_mesh)

                    # Only do it once for MVI
                    if not forward_mesh:
                        backward_fun = set_rotated_operators(
                            backward_fun,
                            neighbors,
                            comp,
                            self.models.gradient_dip,
                            self.models.gradient_direction,
                            forward=False,
                        )
                    average_op = getattr(
                        backward_fun.regularization_mesh,
                        f"aveCC2F{fun.orientation}",
                    )
                    backward_fun.set_weights(**{comp: average_op @ weight})
                    backward_fun.norm = np.round(average_op @ norm, decimals=3)
                    functions.append(backward_fun)

            # Will avoid recomputing operators if the regularization mesh is the same
            forward_mesh = reg_func.regularization_mesh
            reg_func.objfcts = functions
            reg_func.norms = [fun.norm for fun in functions]
            reg_funcs.append(reg_func)

        return objective_function.ComboObjectiveFunction(objfcts=reg_funcs)

    def get_tiles(self):
        n_data = self.inversion_data.mask.sum()
        indices = np.arange(n_data)

        if "2d" in self.params.inversion_type:
            return [indices]

        if "1d" in self.params.inversion_type:
            # Heuristic to avoid too many chunks
            n_chunks = n_data // self.params.compute.max_chunk_size

            if self.params.compute.n_workers:
                n_chunks /= self.params.compute.n_workers
                n_chunks = int(n_chunks) * self.params.compute.n_workers

            n_chunks = np.max([n_chunks, 1])

            return np.array_split(indices, n_chunks)

        return tile_locations(
            self.inversion_data.locations,
            self.params.compute.tile_spatial,
            labels=self.inversion_data.parts,
            sorting=self.simulation.survey.sorting,
        )

    def configure_dask(self):
        """Sets Dask config settings."""

        if self.client:
            dconf.set(scheduler=self.client)
        else:
            n_cpu = self.params.compute.n_cpu
            if n_cpu is None:
                n_cpu = int(multiprocessing.cpu_count())

            dconf.set(scheduler="threads", pool=ThreadPool(n_cpu))

    @classmethod
    def start(cls, filepath: str | Path | InputFile, **kwargs) -> Self:
        """
        Start the inversion driver.

        :param filepath: Path to the input file or InputFile object.
        :param kwargs: Additional keyword arguments for InputFile read_ui_json.

        :return: InversionDriver instance with the specified parameters.
        """
        driver = super().start(filepath, **kwargs)

        return driver

    @staticmethod
    def driver_class_from_name(
        name: str, forward_only: bool = False
    ) -> type[InversionDriver]:
        if name not in DRIVER_MAP:
            msg = f"Inversion type '{name}' is not supported."
            msg += f" Valid inversions are: {(*list(DRIVER_MAP),)}."
            raise NotImplementedError(msg)

        mod_name, classes = DRIVER_MAP.get(name)
        class_name = classes.get("inversion")
        if forward_only:
            class_name = classes.get("forward", class_name)

        module = __import__(mod_name, fromlist=[class_name])
        return getattr(module, class_name)

    @classmethod
    def from_input_file(cls, data: dict) -> type[InversionDriver]:
        forward_only = data.get("forward_only", False)
        inversion_type = data.get("inversion_type", "")
        if inversion_type is None:
            raise GeoAppsError(
                "Key/value 'inversion_type' not found in the input file. "
                "Please specify the inversion type in the UI JSON."
            )

        return cls.driver_class_from_name(inversion_type, forward_only=forward_only)


class InversionLogger:
    """
    Logger for the inversion process.
    """

    def __init__(self, logfile, driver):
        self.driver = driver
        self.terminal = sys.stdout
        self.logfile = self.get_path(logfile)
        self.initial_time = time()

    def start(self):
        date_time = datetime.now().strftime("%b-%d-%Y:%H:%M:%S")
        self.write(
            f"Running simpeg-drivers {__version__}\n"
            f"Started {date_time}\n"
            f"{self.driver.params.title}\n"
        )

    def end(self):
        elapsed_time = timedelta(seconds=time() - self.initial_time).seconds
        days, hours, minutes, seconds = self.format_seconds(elapsed_time)
        self.write(
            f"Total runtime: {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds.\n"
        )

    def write(self, message):
        self.terminal.write(message)
        with open(self.logfile, "a", encoding="utf8") as logfile:
            logfile.write(message)
            logfile.flush()

    @staticmethod
    def format_seconds(seconds):
        days = seconds // (24 * 3600)
        seconds = seconds % (24 * 3600)
        hours = seconds // 3600
        seconds = seconds % 3600
        minutes = seconds // 60
        seconds = seconds % 60
        return days, hours, minutes, seconds

    def close(self):
        self.terminal.close()

    def flush(self):
        pass

    def get_path(self, filepath: str | Path) -> str:
        root_directory = Path(self.driver.workspace.h5file).parent
        return str(root_directory / filepath)


if __name__ == "__main__":
    file = Path(sys.argv[1]).resolve()
    input_file = load_ui_json_as_dict(file)
    n_workers = input_file.get("n_workers", None)
    n_threads = input_file.get("n_threads", None)
    save_report = input_file.get("performance_report", False)

    # Force distributed on 1D problems
    if "1D" in input_file.get("title") and n_workers is None:
        cpu_count = multiprocessing.cpu_count()

        if cpu_count < 16:
            n_threads = n_threads or 2
        else:
            n_threads = n_threads or 4

        n_workers = cpu_count // n_threads

    distributed_process = (
        n_workers is not None and n_workers > 1
    ) or n_threads is not None

    driver_class = InversionDriver.from_input_file(input_file)

    cluster = (
        LocalCluster(
            processes=True,
            n_workers=n_workers,
            threads_per_worker=n_threads,
        )
        if distributed_process
        else None
    )
    profiler = cProfile.Profile()
    profiler.enable()

    with (
        cluster.get_client()
        if cluster is not None
        else contextlib.nullcontext() as context_client
    ):
        # Full run
        with (
            performance_report(filename=file.parent / "dask_profile.html")
            if (save_report and isinstance(context_client, Client))
            else contextlib.nullcontext()
        ):
            driver_class.start(file)
            sys.stdout.close()

    profiler.disable()

    if save_report:
        with open(file.parent / "runtime_profile.txt", encoding="utf-8", mode="w") as s:
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats("cumulative")
            ps.print_stats()
