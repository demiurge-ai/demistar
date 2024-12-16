"""Module defines the `Component` class, this is the base class for `Sensors` and `Actuators`."""

from __future__ import annotations
from abc import ABC
from .resource import Resource

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # from .agent import Agent


class Component(ABC):
    """TODO."""

    def __init__(self, resource: Resource, *args, **kwargs):
        """Constructor.

        Args:
            resource: The resource to attach to the component.
            *args: Additional positional arguments.
            **kwargs: Additional named arguments.
        """
        super().__init__()
        self._resource = resource

    # def attach(self, agent: Agent):
    #     self._agent = agent

    # def detach(self, agent: Agent):
    #     self._agent = None

    # def is_attached(self) -> bool:
    #     return self._agent is not None
