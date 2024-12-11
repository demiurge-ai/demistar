# from demistar.agent.component import Actuator, Sensor
# from demistar.agent.component.component import Component
# from ..event import Observation
# from .agent import Agent
# from .dag import From


# # def _observe(agent: "AsyncAgent", sensor_type: type[Sensor]):
# #     sensor = next(iter(agent.get_sensors(oftype=[sensor_type])), None)
# #     # use the null sensor if no sensor is found? TODO: implement this


# class _ObserveFunction:
#     def __init__(self, sensor: Sensor = None) -> None:
#         self._aiter = sensor.aiter_observations()

#     async def __call__(self) -> Observation:
#         return await self._aiter.__anext__()


# class AsyncAgent(Agent):
#     def __init__(
#         self, sensors: list[Sensor], actuators: list[Actuator], *args, **kwargs
#     ):
#         # for every sensor, we create a function that will yield the most recent observation from that sensor.
#         super().__init__(sensors, actuators, *args, **kwargs)

#         # the compute graph is build from the functions in the agent as well as its sensors and actuators.

#     def add_component(self, component: Component) -> Component:  # noqa
#         component = super().add_component(component)
#         if isinstance(component, Sensor):
#             self._observe_functions[component.id] = _ObserveFunction(component)
#         return component

#     def remove_component(self, component: Component) -> Component:  # noqa
#         if isinstance(component, Sensor):
#             # the observation iteration will be closed below, this will cause AsyncStopIteration
#             # TODO decide what to do with functions that depend on a sensor is removed, this should be handled in the compute graph really.
#             # A sentinal should be returned by the functino indicating that it could not proceed. We can use a special exception for this! and cancel all dependant functions.
#             del self._observe_functions[component.id]
#         return super().remove_component(component)

#     def __cycle__(self):  # noqa: D102
#         pass  # this not used by async agents. Everything is handled by the agents async event loop and relevant functions.
