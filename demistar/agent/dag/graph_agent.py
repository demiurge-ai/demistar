"""Compute graph definition that is specific to agents, it supports dependency injection of Sensors/Actuators into the graph."""

from __future__ import annotations

import inspect

from .from_ import From
from .graph import ComputeGraphHalt
from ..component import Sensor
from ...utils.error import DemistarInternalError
from ...utils._async import EmptyAsyncIterator

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent import Agent


# TODO this will probably be removed in the future when dynamic compute graphs are implemented it will be much simpler to setup the graph for sensors/actuators!
class ComputeGraphAgent:
    """Compute graph for an agent."""

    def __init__(self, agent: Agent):
        """Constructor."""
        self._graph = From.build(agent)
        # locate all From(Sensor) nodes
        _sensor_nodes = set()
        for node in self._graph._graph.nodes:
            if inspect.isclass(node) and issubclass(node, Sensor):
                _sensor_nodes.add(node)
        # replace all sensor nodes initially with an empty _ObserveFunction
        self._node_sensor_map: dict[type, set[_ObservationFunction]] = {}
        for node in _sensor_nodes:
            observe_node = _ObservationFunction.empty()
            # TODO when dynamic compute graphs are properly supported we wont need an empty version of this, the node will just be added to the graph when it is avaliable!
            self._graph.replace_node(node, observe_node)
            # TODO #1 we are using a set here to eventually handle multiple sensors of the same type
            self._node_sensor_map[node] = set([observe_node])

    async def run(self):
        """Run the compute graph."""
        async for func, result in self._graph.run():
            yield func, result

    def on_add_sensor(self, sensor: Sensor):
        """Add a sensor to the compute graph.

        Args:
            sensor (Sensor): The sensor to add to the compute graph.
        """
        # this should be called internally by the agent when a new sensor is added to the agent
        nodes = self._node_sensor_map.get(type(sensor), set())
        assert len(nodes) <= 1  # TODO #1 until we support multiple sensors
        if len(nodes) == 1:
            nodes.pop().set(sensor)

    def on_remove_sensor(self, sensor: Sensor):
        """Remove a sensor from the compute graph.

        Args:
            sensor (Sensor): The sensor to remove from the compute graph.
        """
        # the component will stop its own observation stream when removed from the agent.
        # this will be reflected in the _ObserveFunction which will halt.
        # nothing to do here yet - TODO when dynamic compute graphs are properly
        # supported the sensor node will be removed from the graph here!
        pass


class _ObservationFunction:
    def __init__(self, sensor: Sensor | None):
        self._sensor = sensor
        if sensor is None:
            self._aiter = EmptyAsyncIterator()
        else:
            self._aiter = sensor.aiter_observations()

    async def _empty_aiter(self):
        raise StopAsyncIteration

    def empty() -> _ObservationFunction:
        return _ObservationFunction(None)

    def set(self, sensor: Sensor):
        if self._sensor is not None:
            # this is an internal error that should not happen...
            raise DemistarInternalError(
                f"Cannot replace existing sensor {type(self._sensor)} in computer graph node, instead add a new sensor node to the graph."
            )
        self._sensor = sensor
        self._aiter = sensor.aiter_observations()

    async def __call__(self):
        try:
            return await self._aiter.__anext__()
        except StopAsyncIteration:
            if self._sensor is not None:
                # the sensor has likely been removed from the agent
                assert not self._sensor._observations.is_active()  # sanity check
                self._sensor = None
                self._aiter = EmptyAsyncIterator()
            raise ComputeGraphHalt()
