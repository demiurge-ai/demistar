"""Module defines the `From` class, a core component building compute graphs for agents."""

from typing import Generic, TypeVar
from collections.abc import Callable
from types import GetSetDescriptorType

from ..utils.typing import is_sync_iter, is_async_iter


T = TypeVar("T")
S = TypeVar("S")


class From(Generic[T]):
    """A `From` dependency is an argument of a function that will be resolved to a value at runtime.

    From is effectively a dependency injection mechanism(similar to `Depends` in FastAPI) but with some extra features:

    - a compute graph will be built using `From` and its dependencies - as well as with `demistar.graph.To`.

    It works with the following:
    - properties (or any variable)
    - functions and methods (or any callable)
    - generators (or any iterable)
    - resources (demistar.Resource)
    - sensors (demistar.Sensor)
    - remote objects (ray.remote)
    """

    def __init__(
        self, dependency: Callable[..., T] | property | GetSetDescriptorType | T
    ):
        """Add a dependency to a function.

        Args:
            dependency (Callable[..., T]): dependency that will produce the argument value.
        """
        self._is_iter = False
        self._is_async = False
        if isinstance(dependency, GetSetDescriptorType | property):
            self._func = dependency.fget  # the function
        elif isinstance(dependency, Callable):
            self._func = dependency  # the function
        elif is_sync_iter(dependency):
            self._func = dependency
            self._is_iter = True
        elif is_async_iter(dependency):
            self._func = dependency
            self._is_iter = True
            self._is_async = True
        else:
            # use the value directly - treat it as a constant
            self._func = lambda: dependency

        # this set when the compute graph is built
        self._argument_name = None  # the name of the argument
