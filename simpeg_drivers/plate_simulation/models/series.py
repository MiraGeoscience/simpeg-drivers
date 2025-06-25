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

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from geoh5py import Workspace
from geoh5py.objects import Octree
from geoh5py.shared.utils import fetch_active_workspace

from simpeg_drivers.plate_simulation.models import EventMap
from simpeg_drivers.plate_simulation.models.events import (
    Anomaly,
    Erosion,
    Event,
    Overburden,
)


if TYPE_CHECKING:
    from .events import Deposition


class Series(ABC):
    """
    Sequence of geological events.

    :param history: Sequence of geological events.
    """

    def __init__(self, history: Sequence[Event | Series]):
        self.history = history

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Realize each event in the history.

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the events in the history.
        :param event_map: mapping event ids to names and physical properties.
        """

        for event in self.history:
            model, event_map = event.realize(mesh, model, event_map)

        return model, event_map

    @property
    @abstractmethod
    def history(self):
        """Sequence of geological events."""

    @history.setter
    @abstractmethod
    def history(self, events):
        pass


class Lithology(Series):
    """
    Model a sequence of sedimentary layers.

    :param history: Sequence of layers to be deposited. These should be
        ordered so that the first layer in the list is the bottom unit
        and the last layer is the top unit
    """

    # TODO: Provide an optional bottom surface to begin the deposition.

    def __init__(self, history: Sequence[Deposition]):
        super().__init__(history[::-1])

    @property
    def history(self) -> Sequence[Deposition | Erosion]:
        """Sequence of geological events."""
        return self._history

    @history.setter
    def history(self, events):
        if not all(isinstance(k, Event) for k in events):
            raise ValueError("History must be a sequence of geological events.")

        self._history = events


class DikeSwarm(Series):
    """
    Model a set of dike intrusions.

    :param history: Sequence of intrusions represented by Anomaly objects.
    :param name: Name of the dike swarm.
    """

    def __init__(self, history: Sequence[Anomaly], name: str = "Dike Swarm"):
        super().__init__(history)
        self.name = name

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Realize each event in the history.

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the events in the history.
        :param event_map: mapping event ids to names and physical properties.
        """

        event_id = max(event_map) + 1
        event_map[event_id] = (self.name, self.history[0].value)
        for event in self.history:
            model, event_map = event.realize(mesh, model, event_map, coeval=True)

        return model, event_map

    @property
    def history(self) -> Sequence[Anomaly]:
        """Sequence of geological events."""
        return self._history

    @history.setter
    def history(self, events):
        if not all(isinstance(k, Anomaly) for k in events):
            raise ValueError("History must be a sequence of geological Anomaly.")

        self._history = events


class GeologyViolationError(Exception):
    """Raise when a geological history is invalid."""

    def __init__(self, message):
        super().__init__(message)


class Geology(Series):
    """
    Ensures that a history is valid.

    :param history: Sequence of geological events to be validated.
    """

    def __init__(
        self,
        workspace: Workspace,
        *,
        mesh: Octree,
        background: float,
        history: Sequence[Event | Series],
    ):
        super().__init__(history)
        self.workspace = workspace
        self.mesh = mesh
        self.background = background

    def __iter__(self):
        return iter(self.history)

    @property
    def history(self) -> Sequence[Event | Series]:
        """Sequence of geological events."""
        return self._history

    @history.setter
    def history(self, events):
        if not all(isinstance(k, Event | Series) for k in events):
            raise ValueError(
                "History must be a sequence of geological Event or Series."
            )

        self._validate_history(events)
        self._history = events

    @property
    def mesh(self) -> Octree:
        """Octree mesh on which the model is defined."""
        return self._mesh

    @mesh.setter
    def mesh(self, val: Octree):
        if val.n_cells is None:
            raise ValueError("Mesh must have n_cells.")
        self._mesh = val

    def build(self) -> tuple[np.ndarray, EventMap]:
        """
        Realize the geological events in the scenario.

        :return: Model and event map.
        """
        with fetch_active_workspace(self.workspace, mode="r+"):
            if self.mesh.n_cells is None:
                raise ValueError("Mesh must have n_cells.")
            event_map = {1: ("Background", self.background)}
            geology, event_map = super().realize(
                self.mesh, np.ones(self.mesh.n_cells), event_map
            )

        return geology, event_map

    def _validate_history(self, events: Sequence[Event | Series]):
        """Throw exception if the history isn't valid."""
        self._validate_overburden(events)
        self._validate_topography(events)

    def _validate_overburden(self, events: Sequence[Event | Series]):
        """Throw exception if Overburden is not the second last event in the history."""

        if any(isinstance(k, Overburden) for k in events) and not isinstance(
            events[-2], Overburden
        ):
            raise GeologyViolationError(
                "Overburden events must occur before the final erosion in the history."
            )

    def _validate_topography(self, events: Sequence[Event | Series]):
        """Throw exception if the last event isn't an erosion."""

        if not isinstance(events[-1], Erosion):
            raise GeologyViolationError(
                "The last event in a geological history must be an erosion."
            )
