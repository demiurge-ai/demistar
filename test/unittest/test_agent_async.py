"""Testing agent functionality with DAG."""

from demistar.agent import Agent, Sensor, Actuator, From
from demistar.event import Observation


class StubSensor1(Sensor):
    pass


class StubSensor2(Sensor):
    pass


class StubActuator(Actuator):
    pass


class TestAgent(Agent):
    """Test agent class."""

    def __cycle__(self):  # noqa: D105
        pass

    async def funcA(self):
        return "A"

    async def decide(self, a=From(funcA), obs=From(StubSensor1)):
        return f"Decision({a}, {obs.value})"


if __name__ == "__main__":
    import asyncio

    agent = TestAgent([StubSensor1(), StubSensor2()], [StubActuator()])

    async def sense():
        sensor = agent.get_sensors(oftype=StubSensor1).pop()
        sensor._observations.push(Observation(value=1))
        await asyncio.sleep(1)
        sensor._observations.push(Observation(value=2))
        await asyncio.sleep(1)
        sensor._observations.close()

    async def run():
        async for func, result in agent.__computegraph__.run():
            print("RUN-1", func, result)

        async for func, result in agent.__computegraph__.run():
            print("RUN-2", func, result)

    async def main():
        await asyncio.gather(asyncio.create_task(sense()), asyncio.create_task(run()))

    asyncio.run(main())
