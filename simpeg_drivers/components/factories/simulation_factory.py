# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


# pylint: disable=W0613
# pylint: disable=W0221

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.options import BaseOptions

from pathlib import Path

import numpy as np
from simpeg import maps

from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory


class SimulationFactory(SimPEGFactory):
    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Options object containing SimPEG object parameters.

        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()

        self.solver = None
        if self.factory_type in [
            "direct current pseudo 3d",
            "direct current 3d",
            "direct current 2d",
            "induced polarization 3d",
            "induced polarization 2d",
            "induced polarization pseudo 3d",
            "magnetotellurics",
            "tipper",
            "fdem",
            "tdem",
        ]:
            import pymatsolver.direct as solver_module

            self.solver = getattr(solver_module, params.solver_type)

    def concrete_object(self):
        if self.factory_type in ["magnetic scalar", "magnetic vector"]:
            from simpeg.potential_fields.magnetics import simulation

            return simulation.Simulation3DIntegral

        if self.factory_type == "gravity":
            from simpeg.potential_fields.gravity import simulation

            return simulation.Simulation3DIntegral

        if self.factory_type in ["direct current 3d", "direct current pseudo 3d"]:
            from simpeg.electromagnetics.static.resistivity import simulation

            return simulation.Simulation3DNodal

        if self.factory_type == "direct current 2d":
            from simpeg.electromagnetics.static.resistivity import simulation_2d

            return simulation_2d.Simulation2DNodal

        if self.factory_type in [
            "induced polarization 3d",
            "induced polarization pseudo 3d",
        ]:
            from simpeg.electromagnetics.static.induced_polarization import simulation

            return simulation.Simulation3DNodal

        if self.factory_type == "induced polarization 2d":
            from simpeg.electromagnetics.static.induced_polarization.simulation import (
                Simulation2DNodal,
            )

            return Simulation2DNodal

        if self.factory_type in ["magnetotellurics", "tipper"]:
            from simpeg.electromagnetics.natural_source import simulation

            return simulation.Simulation3DPrimarySecondary

        if self.factory_type in ["fdem"]:
            from simpeg.electromagnetics.frequency_domain import simulation

            return simulation.Simulation3DMagneticFluxDensity

        if self.factory_type in ["fdem 1d"]:
            from simpeg.electromagnetics.frequency_domain import simulation_1d

            return simulation_1d.Simulation1DLayered

        if self.factory_type in ["tdem"]:
            from simpeg.electromagnetics.time_domain import simulation

            return simulation.Simulation3DMagneticFluxDensity

        if self.factory_type in ["tdem 1d"]:
            from simpeg.electromagnetics.time_domain import simulation_1d

            return simulation_1d.Simulation1DLayered

    def assemble_arguments(
        self,
        survey=None,
        receivers=None,
        global_mesh=None,
        local_mesh=None,
        active_cells=None,
        mapping=None,
        tile_id=None,
    ):
        if "1d" in self.factory_type:
            return ()

        mesh = global_mesh if tile_id is None else local_mesh
        return [mesh]

    def assemble_keyword_arguments(
        self,
        survey=None,
        receivers=None,
        global_mesh=None,
        local_mesh=None,
        active_cells=None,
        mapping=None,
        tile_id=None,
    ):
        mesh = global_mesh if tile_id is None else local_mesh
        sensitivity_path = self._get_sensitivity_path(tile_id)

        kwargs = {}
        kwargs["survey"] = survey
        kwargs["sensitivity_path"] = sensitivity_path
        kwargs["max_chunk_size"] = self.params.max_chunk_size
        kwargs["store_sensitivities"] = (
            "forward_only"
            if self.params.forward_only
            else self.params.store_sensitivities
        )
        kwargs["solver"] = self.solver

        if self.factory_type == "magnetic vector":
            kwargs["active_cells"] = active_cells
            kwargs["chiMap"] = maps.IdentityMap(nP=int(active_cells.sum()) * 3)
            kwargs["model_type"] = "vector"
            kwargs["chunk_format"] = "row"

        if self.factory_type == "magnetic scalar":
            kwargs["active_cells"] = active_cells
            kwargs["chiMap"] = maps.IdentityMap(nP=int(active_cells.sum()))
            kwargs["chunk_format"] = "row"

        if self.factory_type == "gravity":
            kwargs["active_cells"] = active_cells
            kwargs["rhoMap"] = maps.IdentityMap(nP=int(active_cells.sum()))
            kwargs["chunk_format"] = "row"

        if "induced polarization" in self.factory_type:
            etamap = maps.InjectActiveCells(
                mesh, active_cells=active_cells, value_inactive=0
            )
            kwargs["etaMap"] = etamap

        if self.factory_type in [
            "direct current 3d",
            "direct current 2d",
            "magnetotellurics",
            "tipper",
            "fdem",
            "tdem",
        ]:
            actmap = maps.InjectActiveCells(
                mesh, active_cells=active_cells, value_inactive=np.log(1e-8)
            )
            kwargs["sigmaMap"] = maps.ExpMap(mesh) * actmap

        if "tdem" in self.factory_type:
            kwargs["t0"] = -receivers.timing_mark * self.params.unit_conversion
            kwargs["time_steps"] = (
                np.round((np.diff(np.unique(receivers.waveform[:, 0]))), decimals=6)
                * self.params.unit_conversion
            )

        if "1d" in self.factory_type:
            kwargs["sigmaMap"] = maps.ExpMap(mesh)
            kwargs["thicknesses"] = local_mesh.h[0][1:][::-1]
            kwargs["topo"] = active_cells[tile_id]

        return kwargs

    def _get_sensitivity_path(self, tile_id: int) -> str:
        """Build path to destination of on-disk sensitivities."""
        out_dir = Path(self.params.workpath) / "sensitivities"

        if tile_id is None:
            sens_path = out_dir / "Tile.zarr"
        else:
            sens_path = out_dir / f"Tile{tile_id}.zarr"

        return str(sens_path)
