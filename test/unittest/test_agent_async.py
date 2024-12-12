"""Testing agent functionality with DAG."""

from demistar.agent import Agent, Sensor, Actuator, From
from demistar.event import Observation

import asyncio
import unittest


class StubSensor1(Sensor):  # noqa
    pass


class StubSensor2(Sensor):  # noqa
    pass


class StubActuator(Actuator):  # noqa
    pass


class TestAgent(Agent):
    """Test agent class."""

    def __cycle__(self):  # noqa: D105
        pass

    async def funcA(self):  # noqa
        return "A"

    async def decide(self, a=From(funcA), obs=From(StubSensor1)):
        """Function that depends on observations from StubSensor1 and funcA."""
        return f"Decision({a}, {obs.value})"


class TestComputeGraph(unittest.TestCase):
    """Unit test for `Agent` compute graph."""

    def setUp(self):  # noqa
        self.agent = TestAgent([StubSensor1(), StubSensor2()], [StubActuator()])

    async def run_agent(self) -> dict:  # noqa
        """Run the compute graph once."""
        results = {}
        async for func, result in self.agent.__computegraph__.run():
            results[func] = result
        return results

    def test_sense(self):
        """Test that the compute graph processes observations correctly."""

        async def _sense():
            sensor = self.agent.get_sensors(oftype=StubSensor1).pop()
            sensor._observations.push(Observation(value=1))
            sensor._observations.push(Observation(value=2))
            sensor._observations.cancel()

        async def _run():
            result = await self.run_agent()
            self.assertEqual(result[self.agent.decide], "Decision(A, 1)")
            result = await self.run_agent()
            self.assertEqual(result[self.agent.decide], "Decision(A, 2)")

        async def _main():
            await asyncio.gather(
                asyncio.create_task(_sense()), asyncio.create_task(_run())
            )

        asyncio.run(_main())


if __name__ == "__main__":
    unittest.main()
