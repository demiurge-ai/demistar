"""Defines the `From` type, which can be used to inject compute dependencies into functions.

Example:
```
    async func_A() -> str:
        asyncio.sleep(1)
        return "A"

    async func_B(a: str = From(func_A)) -> str:
        return B({a})
```
The functions must be async, and chains of dependencies can be created.

See also `agent.dag.ComputeGraph`.
"""

from typing import Callable, Any, Generic, TypeVar  # noqa: UP035

import inspect

from demistar.agent.component.sensor import Sensor
from .graph import ComputeGraph

T = TypeVar("T")


class From(Generic[T]):
    """A `From` dependency is an argument of a function that will be resolved to a value at runtime.

    See `agent.dag.ComputeGraph` for more information.
    """

    def __init__(self, func: Callable[..., T]):
        """Add a dependency to a function.

        Args:
            func (Callable[..., T]): function that will produce the argument value.
        """
        self._func = func  # the function
        self._argument_name = None  # the name of the argument

    @classmethod
    def build(
        cls, instance: Any, _wrap: Callable[[Callable], Any] | None = None
    ) -> ComputeGraph:
        """Build the compute graph for the given instance or function."""
        if _wrap is None:
            _wrap = lambda x: x  # noqa :)

        graph = ComputeGraph()
        if inspect.isfunction(instance):
            # some dependencies were found, we can build the graph for this!
            graph = _build_for_function(instance, graph, _wrap)
            if graph.is_empty():
                raise ValueError(f"Function: {instance} has no named `From` arguments")
        else:
            graph = _build_for_instance(instance, graph, _wrap)
        return graph

    @classmethod
    def resolve_dependencies(cls, func: Callable) -> dict[str, "From"]:
        """Resolve `From` dependencies of the given function.

        Args:
            func (Callable): function to resolve dependencies for.

        Returns:
            dict[str, From]: the From dependencies for the given function, empty if none were found.
        """
        dependencies = {}
        # get `From` dependencies - these parameters will be passed as arguments to the function
        signature = inspect.signature(func)
        for name, param in signature.parameters.items():
            if isinstance(param.default, From):
                param.default._argument_name = name
                dependencies[name] = param.default
        return dependencies

    def try_bind(self, instance: Any) -> Callable:
        """Attempts to bind the given instance to the inner function."""
        bound_func = getattr(instance, self._func.__name__, None)
        if bound_func is None:
            raise ValueError(
                f"Function { self._func.__name__} was not found in instance of type: {type(instance)}"
            )
        if bound_func.__func__ != self._func:
            raise ValueError(
                f"Function {self._func.__name__} was not found in instance of type: {type(instance)}, perhaps it was modified dynamically?"
            )
        from_ = From(bound_func)
        from_._argument_name = self._argument_name
        return from_

    def __str__(self) -> str:  # noqa: D105
        return f"From({self._argument_name}->{self._func})"

    def __repr__(self) -> str:  # noqa: D105
        return f"From({self._argument_name}->{self._func})"


class Observe(From):
    """A `From` dependency that uses the most recent observation from a sensor of a given type."""

    def __init__(self, sensor: type[Sensor]):
        super().__init__(sensor)


def _build_for_instance(
    instance: Any, graph: ComputeGraph, _wrap: Callable[[Callable], Any]
) -> ComputeGraph:
    functions = {
        func.__func__: func
        for _, func in inspect.getmembers(instance, predicate=inspect.ismethod)
    }

    for _, func in functions.items():
        dependencies = From.resolve_dependencies(func)
        for arg_name, from_ in dependencies.items():
            if from_._func in functions:
                # use the bound function for the given instance
                bound_func = functions[from_._func]
                graph.add_edge(_wrap(bound_func), arg_name, _wrap(func))
            else:
                graph.add_edge(_wrap(from_._func), arg_name, _wrap(func))
                _build_for_function(from_._func, graph, _wrap)

    return graph


def _build_for_function(
    func: Callable, graph: ComputeGraph, _wrap: Callable[[Callable], Any]
) -> ComputeGraph:
    for arg_name, from_ in From.resolve_dependencies(func).items():
        # all functions will already be bound
        graph.add_edge(_wrap(from_._func), arg_name, _wrap(func))
        _build_for_function(from_._func, graph, _wrap)
    return graph
