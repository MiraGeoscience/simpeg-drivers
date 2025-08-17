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

from gc import is_finalized
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.options import BaseOptions

import numpy as np
import simpeg.electromagnetics.time_domain as tdem
from geoh5py.objects.surveys.electromagnetics.airborne_fem import AirborneFEMReceivers
from geoh5py.objects.surveys.electromagnetics.ground_tem import (
    LargeLoopGroundTEMTransmitters,
)
from scipy.interpolate import interp1d

from simpeg_drivers.components.factories.receiver_factory import ReceiversFactory
from simpeg_drivers.components.factories.simpeg_factory import SimPEGFactory
from simpeg_drivers.components.factories.source_factory import SourcesFactory


class SurveyFactory(SimPEGFactory):
    """Build SimPEG sources objects based on factory type."""

    dummy = -999.0

    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Options object containing SimPEG object parameters.
        """
        super().__init__(params)
        self.simpeg_object = self.concrete_object()
        self.local_index = None
        self.survey = None
        self.ordering = None
        self.sorting = None

    def concrete_object(self):
        if self.factory_type in ["magnetic vector", "magnetic scalar"]:
            from simpeg.potential_fields.magnetics import survey

        elif self.factory_type == "gravity":
            from simpeg.potential_fields.gravity import survey

        elif "direct current" in self.factory_type:
            from simpeg.electromagnetics.static.resistivity import survey

        elif "induced polarization" in self.factory_type:
            from simpeg.electromagnetics.static.induced_polarization import survey

        elif "fdem" in self.factory_type:
            from simpeg.electromagnetics.frequency_domain import survey

        elif "tdem" in self.factory_type:
            from simpeg.electromagnetics.time_domain import survey

        elif self.factory_type in ["magnetotellurics", "tipper"]:
            from simpeg.electromagnetics.natural_source import survey

        else:
            raise ValueError(f"Factory type '{self.factory_type}' not recognized.")

        return survey.Survey

    def assemble_arguments(self, data=None):
        """Provides implementations to assemble arguments for receivers object."""
        if "current" in self.factory_type or "polarization" in self.factory_type:
            return self._dcip_arguments(data=data)
        elif "tdem" in self.factory_type:
            return self._tdem_arguments(data=data)
        elif self.factory_type in ["magnetotellurics", "tipper"]:
            return self._naturalsource_arguments(data=data)
        elif "fdem" in self.factory_type:
            return self._fem_arguments(data=data)
        else:  # Gravity and Magnetic
            receivers = ReceiversFactory(self.params).build(
                locations=data.locations,
                data=data.observed,
            )
            sources = SourcesFactory(self.params).build(receivers=receivers)
            n_rx = data.locations.shape[0]
            n_comp = len(data.components)
            self.ordering = np.c_[
                np.zeros(n_rx * n_comp),  # Single channel
                np.kron(np.ones(n_rx), np.arange(n_comp)),  # Components
                np.kron(np.arange(n_rx), np.ones(n_comp)),  # Receivers
            ].astype(int)
            self.sorting = np.arange(n_rx, dtype=int)

            return [sources]

    def assemble_keyword_arguments(self, **_):
        """Implementation of abstract method from SimPEGFactory."""
        return {}

    def build(
        self,
        data=None,
    ):
        """Overloads base method to add dobs, std attributes to survey class instance."""
        survey = super().build(
            data=data,
        )
        survey.n_channels = len(
            data.normalizations
        )  # Either time channels or frequencies
        survey.n_components = len(data.components)
        if not self.params.forward_only:
            self._add_data(survey, data)

        survey.dummy = self.dummy

        return survey

    def _add_data(self, survey, data):
        # Stack the data by [channel, component, receiver]
        data_stack = np.dstack(
            [np.vstack(list(k.values())) for k in data.observed.values()]
        ).transpose((0, 2, 1))
        uncert_stack = np.dstack(
            [np.vstack(list(k.values())) for k in data.uncertainties.values()]
        ).transpose((0, 2, 1))

        # Reorder the data and uncertainties based on the ordering
        # of the SimPEG sources and receivers
        data_vec = data_stack[
            self.ordering[:, 0], self.ordering[:, 1], self.ordering[:, 2]
        ]
        uncertainty_vec = uncert_stack[
            self.ordering[:, 0], self.ordering[:, 1], self.ordering[:, 2]
        ]
        uncertainty_vec[np.isnan(data_vec)] = np.inf
        data_vec[np.isnan(data_vec)] = self.dummy  # Nan's handled by inf uncertainties
        survey.dobs = data_vec
        survey.std = uncertainty_vec

    def _dcip_arguments(self, data=None):
        if getattr(data, "entity", None) is None:
            return None

        receiver_entity = data.entity
        source_ids, order = np.unique(
            receiver_entity.ab_cell_id.values, return_index=True
        )
        currents = receiver_entity.current_electrodes

        if "2d" in self.params.inversion_type:
            receiver_locations = data.drape_locations(receiver_entity.vertices)
            source_locations = data.drape_locations(currents.vertices)
        else:
            receiver_locations = receiver_entity.vertices
            source_locations = currents.vertices

        sources = []
        sorting = []
        for source_id in source_ids[np.argsort(order)]:  # Cycle in original order
            receiver_indices = np.where(receiver_entity.ab_cell_id.values == source_id)[
                0
            ]

            if len(receiver_indices) == 0:
                continue

            sorting.append(receiver_indices)
            receivers = ReceiversFactory(self.params).build(
                locations=receiver_locations,
                local_index=receiver_entity.cells[receiver_indices],
            )

            if receivers.nD == 0:
                continue

            if "induced polarization" in self.factory_type:
                receivers.data_type = "apparent_chargeability"

            cell_ind = currents.ab_cell_id.values == source_id
            source = SourcesFactory(self.params).build(
                receivers=receivers,
                locations=source_locations[currents.cells[cell_ind].flatten()],
            )
            sources.append(source)

        self.ordering = np.c_[
            np.zeros(receiver_entity.n_cells),  # Single channel
            np.zeros(receiver_entity.n_cells),  # Single component
            np.hstack(sorting),  # Multi-receivers
        ].astype(int)
        self.sorting = np.hstack(sorting).astype(int)
        return [sources]

    def _tdem_arguments(self, data=None):
        receivers = data.entity
        transmitters = receivers.transmitters

        if receivers.channels[-1] > (
            receivers.waveform[:, 0].max() - receivers.timing_mark
        ):
            raise ValueError(
                f"The latest time channel {receivers.channels[-1]} exceeds "
                f"the waveform discretization. Revise waveform."
            )

        if isinstance(transmitters, LargeLoopGroundTEMTransmitters):
            if receivers.tx_id_property is None:
                raise ValueError(
                    "Transmitter ID property required for LargeLoopGroundTEMReceivers"
                )

            tx_rx = receivers.tx_id_property.values
            tx_ids = transmitters.tx_id_property.values
            sorting = []
            tx_locs = []
            for tx_id in np.unique(tx_rx):
                sorting.append(np.where(tx_rx == tx_id)[0])
                tx_ind = tx_ids == tx_id
                loop_cells = transmitters.cells[
                    np.all(tx_ind[transmitters.cells], axis=1), :
                ]
                loop_ind = np.r_[loop_cells[:, 0], loop_cells[-1, 1]]
                tx_locs.append(transmitters.vertices[loop_ind, :])
        else:
            # Assumes 1:1 mapping of tx to rx
            sorting = np.arange(receivers.n_vertices).tolist()
            tx_locs = transmitters.vertices

        wave_times = (
            receivers.waveform[:, 0] - receivers.timing_mark
        ) * self.params.unit_conversion

        if "1d" in self.factory_type:
            on_times = wave_times <= 0.0
            waveform = tdem.sources.PiecewiseLinearWaveform(
                times=wave_times[on_times],
                currents=receivers.waveform[on_times, 1],
            )
        else:
            wave_function = interp1d(
                wave_times,
                receivers.waveform[:, 1],
                fill_value="extrapolate",
            )

            waveform = tdem.sources.RawWaveform(
                waveform_function=wave_function, offTime=0.0
            )

        tx_list = []
        rx_factory = ReceiversFactory(self.params)
        tx_factory = SourcesFactory(self.params)
        ordering = []
        for cur_tx_locs, rx_ids in zip(tx_locs, sorting, strict=True):
            locs = receivers.vertices[rx_ids, :]
            rx_list = []

            for comp_id, component in enumerate(data.components):
                rx_obj = rx_factory.build(
                    locations=locs,
                    data=data,
                    component=component,
                )
                rx_obj.local_index = rx_ids
                rx_list.append(rx_obj)
                n_times = len(receivers.channels)
                n_rx = len(rx_ids) if isinstance(rx_ids, np.ndarray) else 1
                ordering.append(
                    np.c_[
                        np.kron(np.arange(n_times), np.ones(n_rx)),
                        np.ones(n_times * n_rx) * comp_id,
                        np.kron(np.ones(n_times), np.asarray(rx_ids)),
                    ]
                )

            tx_list.append(
                tx_factory.build(rx_list, locations=cur_tx_locs, waveform=waveform)
            )

        self.ordering = np.vstack(ordering).astype(int)
        self.sorting = np.hstack(sorting).astype(int)
        return [tx_list]

    def _fem_arguments(self, data=None):
        channels = np.array(data.entity.channels)
        rx_locs = data.entity.vertices
        tx_locs = data.entity.transmitters.vertices
        frequencies = data.entity.transmitters.workspace.get_entity("Tx frequency")[0]
        frequencies = np.array(
            [int(frequencies.value_map[f]) for f in frequencies.values]
        )

        sources = []
        rx_factory = ReceiversFactory(self.params)
        tx_factory = SourcesFactory(self.params)
        receiver_groups = []
        block_ordering = []
        for rx_id, locs in enumerate(rx_locs):
            receivers = []
            for comp_id, component in enumerate(data.components):
                receiver = rx_factory.build(
                    locations=locs,
                    data=data,
                    component=component,
                )

                receiver.local_index = rx_id
                block_ordering.append([comp_id, rx_id])
                receivers.append(receiver)

            receiver_groups.append(receivers)

        block_ordering = np.vstack(block_ordering)
        ordering = []
        for freq_id, frequency in enumerate(channels):
            for rx_id, receivers in enumerate(receiver_groups):
                locs = tx_locs[frequency == frequencies, :][rx_id, :]
                sources.append(
                    tx_factory.build(
                        receivers,
                        locations=locs,
                        frequency=frequency,
                    )
                )

            ordering.append(
                np.hstack(
                    [
                        np.ones((block_ordering.shape[0], 1)) * freq_id,
                        block_ordering,
                    ]
                )
            )

        self.ordering = np.vstack(ordering).astype(int)
        self.sorting = np.arange(rx_locs.shape[0], dtype=int)
        return [sources]

    def _naturalsource_arguments(self, data=None):
        simpeg_mt_translate = {
            "zxx_real": "zyy_real",
            "zxx_imag": "zyy_imag",
            "zxy_real": "zyx_real",
            "zxy_imag": "zyx_imag",
            "zyx_real": "zxy_real",
            "zyx_imag": "zxy_imag",
            "zyy_real": "zxx_real",
            "zyy_imag": "zxx_imag",
        }
        receivers = []
        sources = []
        rx_factory = ReceiversFactory(self.params)
        tx_factory = SourcesFactory(self.params)
        block_ordering = []
        self.sorting = np.arange(data.locations.shape[0], dtype=int)
        for comp_id, comp in enumerate(data.components):
            receivers.append(
                rx_factory.build(
                    locations=data.locations,
                    data=data,
                    component=simpeg_mt_translate.get(comp, comp),
                )
            )
            block_ordering.append(
                np.c_[np.ones_like(self.sorting) * comp_id, self.sorting]
            )

        block_ordering = np.vstack(block_ordering)
        ordering = []

        for freq_id, frequency in enumerate(data.entity.channels):
            sources.append(tx_factory.build(receivers, frequency=frequency))
            ordering.append(
                np.hstack(
                    [
                        np.ones((block_ordering.shape[0], 1)) * freq_id,
                        block_ordering,
                    ]
                )
            )

        self.ordering = np.vstack(ordering).astype(int)

        return [sources]
