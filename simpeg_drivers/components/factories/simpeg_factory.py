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
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from geoapps_utils.driver.params import BaseParams

    from simpeg_drivers.params import BaseOptions

# TODO Redesign simpeg factory to avoid pylint arguments-differ complaint


class SimPEGFactory(ABC):
    """
    Build SimPEG objects based on inversion type.

    Parameters
    ----------
    params :
        Driver parameters object.
    factory_type :
        Concrete factory type.
    simpeg_object :
        Abstract SimPEG object.

    Methods
    -------
    assemble_arguments():
        Assemble arguments for SimPEG object instantiation.
    assemble_keyword_arguments():
        Assemble keyword arguments for SimPEG object instantiation.
    build():
        Generate SimPEG object with assembled arguments and keyword arguments.
    """

    valid_factory_types = [
        "gravity",
        "magnetic scalar",
        "magnetic vector",
        "direct current pseudo 3d",
        "direct current 3d",
        "direct current 2d",
        "induced polarization 3d",
        "induced polarization 2d",
        "induced polarization pseudo 3d",
        "fem",
        "tdem",
        "magnetotellurics",
        "tipper",
        "joint surveys",
        "joint cross gradient",
    ]

    def __init__(self, params: BaseParams | BaseOptions):
        """
        :param params: Driver parameters object.
        """
        self.params = params
        self.factory_type: str = params.inversion_type
        self.simpeg_object = None

    @property
    def factory_type(self):
        return self._factory_type

    @factory_type.setter
    def factory_type(self, val):
        if val not in self.valid_factory_types:
            msg = f"Factory type: {val} not implemented yet."
            raise NotImplementedError(msg)
        else:
            self._factory_type = val

    @abstractmethod
    def concrete_object(self):
        """To be over-ridden in factory implementations."""

    @abstractmethod
    def assemble_arguments(self, _) -> list:
        """To be over-ridden in factory implementations."""

    @abstractmethod
    def assemble_keyword_arguments(self, **_) -> dict:
        """To be over-ridden in factory implementations."""

    def build(self, **kwargs):
        """To be over-ridden in factory implementations."""

        class_args = self.assemble_arguments(**kwargs)
        class_kwargs = self.assemble_keyword_arguments(**kwargs)
        return self.simpeg_object(  # pylint: disable=not-callable
            *class_args, **class_kwargs
        )
