#  Copyright (c) 2022-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from geoh5py.ui_json.utils import fetch_active_workspace
from SimPEG.objective_function import ComboObjectiveFunction

from simpeg_drivers.components.methods.magnetics import MagneticScalarMisfit
from simpeg_drivers.driver import InversionDriver

from .params import MagneticScalarParams


class MagneticScalarDriver(InversionDriver):
    _params_class = MagneticScalarParams
    _misfit_factory = MagneticScalarMisfit

    def __init__(self, params: MagneticScalarParams):
        super().__init__(params)

    @property
    def data_misfit(self) -> ComboObjectiveFunction:
        """The Simpeg.data_misfit class"""
        if getattr(self, "_data_misfit", None) is None:
            with fetch_active_workspace(self.workspace, mode="r+"):
                tiles = [None]

                if self.params.tile_spatial > 1:
                    tiles = self.get_tiles()
                else:
                    # Just here to call the random seed. Need to update the targets
                    # after removing this.
                    self.get_tiles()

                local_misfits = []
                self._sorting = []
                self._ordering = []
                multipliers = []

                for tile_num, local_index in enumerate(tiles):
                    factory = self._misfit_factory(self, local_index, tile_num)
                    local_misfit = factory.build()
                    local_misfits.append(local_misfit)

                    multiplier = 1.0

                    if self.params.tile_spatial > 1:
                        multiplier = (
                            local_misfit.model_map.shape[0]
                            / local_misfit.model_map.shape[1]
                        )

                    multipliers.append(multiplier)
                    self._sorting.append(factory.indices)
                    self._ordering.append(factory.ordering)

                self._data_misfit = ComboObjectiveFunction(
                    local_misfits, multipliers=multipliers
                )

        return self._data_misfit
