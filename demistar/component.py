from __future__ import annotations
from abc import ABC
from .resource import Resource

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent


class Component(ABC):
    def __init__(self, resource: Resource, *args, **kwargs):
        super().__init__()
        self._resource = resource

    def attach(self, agent: Agent):
        self._agent = agent

    def detach(self, agent: Agent):
        self._agent = None

    def is_attached(self) -> bool:
        return self._agent is not None
