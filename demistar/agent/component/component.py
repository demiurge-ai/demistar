"""Module defining the class `Component`, see class documentation for details."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...event import Observation, Action, Event
from ._observations import _Observations
from ...utils import int64_uuid

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment import State

__all__ = ("Component",)


class Component(ABC):
    """Base class for components that may be attached to an agent.

    Components include: `Sensor` and `Actuator`, which are used by the agent for sensing the environment and performing actions to change its state.
    """

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        self._id: int = int64_uuid()
        # this will be set by the agent when this component is added to it.
        # generally it should not be accessed directly unless you know what you are doing!
        self._agent = None
        # actions to attempt in the current cycle to produce observations
        self._actions: list[Action] = []  # TODO allow async access here?
        # observations that result from taking action
        self._observations: _Observations = _Observations()

    def on_add(self, agent: Agent) -> None:
        """Callback for when this `Component` is added to an `Agent`.

        Args:
            agent (Agent): agent that this `Component` was added to.
        """
        self._agent = agent

    def on_remove(self, agent: Agent) -> None:
        """Callback for when this `Component` is removed from an `Agent`.

        Args:
            agent (Agent): agent that this `Component` was removed from to.
        """
        self._agent = None
        self._observations.cancel()

    @property
    def id(self):
        """Unique identifier for this [`Component`].

        Returns:
            [str]: unique identifier
        """
        return self._id

    def iter_observations(self):
        """Iterate over and consumes the observations that are currently buffered in this `Component`.

        Yields:
            [Observation]: the most recent observation.
        """
        for observation in self._observations:
            yield self.__transduce__(observation)

    def iter_actions(self):
        """Iterates (and consumes?TODO) the actions that are currently buffered in this `Component`.

        Yields:
            [Action]: the most recent action.
        """
        yield from filter(None, self._actions)

    async def aiter_observations(self):
        """Iterate over and consumes the observations that arrive at this component. This will run until the component is removed from the agent. It will not be possible to consume observations in any other way (i.e. not via `iter_observations`) while this is running.

        Yields:
            Observation: the most recent observation.
        """
        async for item in self._observations:
            yield self.__transduce__(item)

    async def aiter_actions(self):
        """Not implemented."""
        # TODO
        raise NotImplementedError("TODO")

    def __transduce__(self, observation: Observation) -> Observation:
        """Transform an incoming observation into another observation. This is typically used to implement a transformation of "raw" observations that this component may receive. There is no restriction on how this transformation is done.

        Args:
            observation (Observation): observation to transform

        Returns:
            Observation: the transformed observation
        """
        return observation

    @abstractmethod
    def __query__(self, state: State) -> None:
        """Query the state of the environment (take an action).

        This should not be called manually, and is instead part of the agent's cycle.

        Args:
            state (State): state of the environment.
        """

    def __str__(self):  # noqa: D105
        return f"{self.__class__.__name__}({self._id})"

    def __repr__(self):  # noqa: D105
        return str(self)

    @staticmethod
    def set_event_source(component: Component, events: list[Event]):
        """Set the `source` attribute of each event in `events` to be the `id` of this `Component`. Typically `component` is the component that is taking the actions.

        Args:
            component (Component): that is taking the actions
            events (list[Event]): whoses sources should be set
        """
        for event in events:
            event.source = (component.id << 64) | component._agent.id

    @staticmethod
    def unpack_event_source(event: Event):
        """Unpack the source of an action into the component id and agent id.

        Args:
            event (Event): event with source to unpack

        Returns:
            tuple[int, int]: (component id, agent id)
        """
        component_id = event.source >> 64
        agent_id = event.source & 0xFFFFFFFFFFFFFFFF
        return component_id, agent_id
