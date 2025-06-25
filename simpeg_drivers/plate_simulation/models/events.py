# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2025 Mira Geoscience Ltd.                                          '
#                                                                                   '
#  This file is part of simpeg-drivers package.                                     '
#                                                                                   '
#  simpeg-drivers is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                      '
#                                                                                   '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from abc import ABC, abstractmethod

import numpy as np
from geoh5py.objects import Octree, Surface
from geoh5py.shared.utils import find_unique_name

from simpeg_drivers.plate_simulation.models import EventMap
from simpeg_drivers.plate_simulation.models.parametric import Boundary, Parametric


class Event(ABC):
    """
    Parameterized geological events that modify the model.

    :param value: Physical property value assigned to the event.
    :param name: Name of the event.
    """

    def __init__(self, value: float, name: str):
        self.value = value
        self.name = name

    def _update_event_map(self, event_map: EventMap) -> tuple[int, EventMap]:
        """
        Increase the event id and add name and physical property to the event map.

        :param event_map: mapping event ids to names and physical properties.

        :return: Updated event id.
        :return: Updated event map.
        """

        event_id = max(event_map) + 1
        names = [elem[0] for elem in event_map.values()]
        name = find_unique_name(self.name, names)
        event_map[event_id] = (name, self.value)

        return event_id, event_map

    @abstractmethod
    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Update the model with the event realization

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the event.
        :param event_map: mapping event ids to names and physical properties.

        :return: Updated model and list of events including itself.
        """


class Deposition(Event):
    """
    Fills model below a surface with a provided property value.

    :param surface: Surface representing the top of a sedimentary layer.
    :param value: The value given to the model below the surface.
    :param name: Name of the event.
    """

    def __init__(self, surface: Surface, value: float, name: str = "Deposition"):
        self.surface = Boundary(surface)
        super().__init__(value, name)

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Implementation of parent Event abstract method.
        Fill the model below the surface with the layer's value.
        """

        event_id, event_map = self._update_event_map(event_map)
        model[self.surface.mask(mesh)] = event_id

        return model, event_map


class Overburden(Event):
    """
    Add an overburden layer below the topography surface.

    :param topography: Surface representing the topography.
    :param thickness: Thickness of the overburden layer.
    :param value: Model value given to the overburden layer.
    :param name: Name of the event.
    """

    def __init__(
        self,
        topography: Surface,
        thickness: float,
        value: float,
        name: str = "Overburden",
    ):
        self.topography = Boundary(topography)
        self.thickness = thickness
        super().__init__(value, name)

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Implementation of parent Event abstract method.
        Fill the model below the topography with the overburden value.
        """
        event_id, event_map = self._update_event_map(event_map)
        model[
            ~self.topography.mask(mesh, offset=-1 * self.thickness, reference="center")
        ] = event_id

        return model, event_map


class Erosion(Event):
    """
    Erode the model at a provided surface.

    :param surface: The surface above which the model will be
        eroded (filled with nan values).
    :param value: The value given to the eroded model, default to nan.
    :param name: Name of the Erosion event.
    """

    def __init__(self, surface: Surface, value: float = np.nan, name: str = "Erosion"):
        self.surface = Boundary(surface)
        super().__init__(value, name)

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap
    ) -> tuple[np.ndarray, EventMap]:
        """
        Implementation of parent Event abstract method.
        Fill the model above the surface with nan values.
        """

        event_id, event_map = self._update_event_map(event_map)
        model[~self.surface.mask(mesh)] = event_id

        return model, event_map


class Anomaly(Event):
    """
    Enrich or deplete the model within a close body.

    :param body: Closed body within which the model will be filled
        with the anomaly value.
    :param value: Model value assigned to the anomaly.
    :param name: Name of the event.
    """

    def __init__(self, body: Parametric, value: float, name: str = "Anomaly"):
        self.body = body
        super().__init__(value, name)

    def realize(
        self, mesh: Octree, model: np.ndarray, event_map: EventMap, coeval: bool = False
    ) -> tuple[np.ndarray, EventMap]:
        """
        Implementation of parent Event abstract method.
        Fill the model within the surface with the anomaly value.
        """

        if coeval:
            event_id = max(event_map)
        else:
            event_id, event_map = self._update_event_map(event_map)

        model[self.body.mask(mesh)] = event_id

        return model, event_map
