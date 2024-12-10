"""Test `Component` classes."""

import copy
import unittest
from typing import Any
from demistar.agent import Actuator, Sensor, attempt
from demistar.event import Event
from unittest.mock import MagicMock

from demistar.pubsub import Subscribe


class MyActuator(Actuator):
    """Test actuator."""

    @attempt()
    def foo(self, action: Any):  # noqa: D102
        return action


class MySensor(Sensor):
    """Test sensor."""

    def __subscribe__(self) -> list[Subscribe]:  # noqa: D105
        return [Subscribe(topic="mytopic")]

    @attempt()
    def bar(self, action: Any):  # noqa: D102
        return action


class TestComponents(unittest.TestCase):
    """Unit tests for sensors and actuators."""

    def test_sensor_cycle(self):
        """Test __cycle__ method in Sensor."""
        state = MagicMock()
        agent = MagicMock()
        action1 = Event()
        action2 = Event()
        state.__select__ = lambda actions: actions
        sensor = MySensor()
        # simulate adding the sensor to the agent
        sensor.on_add(agent)
        # take action 1
        a = sensor.bar(action1)
        self.assertEqual(action1, a)
        # take action 2
        a = sensor.bar(action2)  # take again
        actions = copy.deepcopy(list(sensor.iter_actions()))
        self.assertEqual(actions[0].topic, "mytopic")
        self.assertListEqual(actions[1:], [action1, action2])

        self.assertEqual(action2, a)
        # query environment (itll just return the actions again)
        sensor.__query__(state)
        observations = list(sensor.iter_observations())
        self.assertEqual(observations[0].topic, "mytopic")
        self.assertListEqual(observations[1:], [action1, action2])

    def test_actuator_cycle(self):
        """Test __cycle__ method in Actuator."""
        state = MagicMock()
        agent = MagicMock()
        agent.id = 0
        action1 = Event()
        action2 = Event()
        state.__update__ = lambda actions: actions
        actuator = MyActuator()
        # simulate adding the actuator to the agent
        actuator.on_add(agent)
        # take action 1
        a = actuator.foo(action1)
        self.assertEqual(action1, a)
        # take action 2
        a = actuator.foo(action2)  # take again
        self.assertEqual(action2, a)
        actions = copy.deepcopy(list(actuator.iter_actions()))
        self.assertListEqual(actions, [action1, action2])

        # query environment (itll just return the actions again)
        actuator.__query__(state)
        observations = list(actuator.iter_observations())
        self.assertListEqual(observations, [action1, action2])


if __name__ == "__main__":
    unittest.main()
