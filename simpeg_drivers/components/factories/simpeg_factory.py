#  Copyright (c) 2023-2024 Mira Geoscience Ltd.
#
#  This file is part of simpeg_drivers package.
#
#  All rights reserved

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpeg_drivers.driver import InversionDriver

# TODO Redesign simpeg factory to avoid pylint arguments-differ complaint


class SimPEGFactory(ABC):
    """
    Build SimPEG objects based on inversion type.

    Parameters
    ----------
    driver :
        Driver parameters object.

    Methods
    -------
    assemble_arguments():
        Assemble arguments for SimPEG object instantiation.
    assemble_keyword_arguments():
        Assemble keyword arguments for SimPEG object instantiation.
    build():
        Generate SimPEG object with assembled arguments and keyword arguments.
    """

    concrete_type: type

    def __init__(self, driver: InversionDriver):
        """
        :param driver: A driver class.
        """
        self.driver = driver

    @abstractmethod
    def concrete_object(self):
        """To be over-ridden in factory implementations."""

    @abstractmethod
    def assemble_arguments(self, _) -> list:
        """To be over-ridden in factory implementations."""

    @abstractmethod
    def assemble_keyword_arguments(self, **_) -> dict:
        """To be over-ridden in factory implementations."""

    @classmethod
    def build(cls, driver, **kwargs):
        """Collect arguments and keyword arguments and build SimPEG object."""
        class_args = cls.assemble_arguments(driver, **kwargs)
        class_kwargs = cls.assemble_keyword_arguments(driver, **kwargs)
        return cls.concrete_type(*class_args, **class_kwargs)
