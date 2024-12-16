"""Module defines the `Actuator` class, this is a `Component` that can write/send data to a `Resource`."""

from .component import Component
from .resource import Resource


class Actuator(Component):
    """TODO."""

    def __init__(self, resource: Resource, *args, **kwargs):
        """Constructor.

        Args:
            resource: The resource to attach to the component.
            *args: Additional positional arguments.
            **kwargs: Additional named arguments.
        """
        super().__init__(resource, *args, **kwargs)
