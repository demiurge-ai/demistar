"""Basic components of an agent: Sensor & Actuator.

- Sensors receive data from the resource (sense)
- Actuators send data to the resource (act)
"""

from .resource import Resource


class Actuator:
    def __init__(self, resource: Resource, *args, **kwargs):
        super().__init__()
        self._resource = resource
