from typing import Callable
from collections import defaultdict
from fastapi import Request
import inspect


def sense(route: str = None):
    def decorator(func):
        func._routing_info = {
            "route": route,
            "func": func,
            "type": "sensor",
            "dependencies": From.get_dependencies(func),
        }
        return func

    return decorator


def attempt(route: str = None):
    def decorator(func):
        func._routing_info = {
            "route": route,
            "func": func,
            "name": f"{func.__module__}.{func.__qualname__}",
            "type": "actuator",
            "dependencies": From.get_dependencies(func),
        }
        return func

    return decorator


class From:
    def __init__(self, func: Callable):
        super().__init__()
        self.key = None
        self.func = func

    @classmethod
    def new(cls, func: Callable, key: str):
        from_ = From(func)
        from_.key = key
        return from_

    @classmethod
    def get_dependencies(cls, func):
        dependencies = []
        # get `From` dependencies - these parameters will be passed as arguments to the function
        signature = inspect.signature(func)
        for name, param in signature.parameters.items():
            if isinstance(param.default, From):
                dependencies.append(From.new(param.default.func, name))
        return dependencies

    def __str__(self) -> str:
        return f"From({self.key}->{self.func})"

    def __repr__(self) -> str:
        return f"From({self.key}->{self.func})"


class Route:
    def __init__(self, sense, attempt, dependency_graph):
        super().__init__()
        assert sense["type"] == "sensor"
        assert attempt["type"] == "actuator"
        assert sense["route"] == attempt["route"]

        self._sense = sense
        self._attempt = attempt
        # locate all the attempt functions - these are the end points of the execution graph, they return actions"
        self._attempt_functions = []
        print(dependency_graph)

    async def __call__(self, request: Request):
        pass
        # build the execution tree
        # self._resolve_backwards(request, self._attempt)
        # start with the attempt function, and resolve its dependencies all the way back to the sense function with request as the first argument!

    # async def _resolve_backwards(self, request, info):
    #     func = info["func"]
    #     # get dependencies of func
    #     print(func)
    #     print("dependencies", info["dependencies"])

    #     kwargs = {}
    #     for _from in info["dependencies"]:
    #         key, _dep = _from.key, _from.func
    #         value = await self._resolve_backwards(request, _dep)
    #         kwargs[key] = value

    #     if func == self._sense["func"]:
    #         return await func(request, **kwargs)
    #     else:
    #         return await func(**kwargs)

    #     # call all functions that the original sense function depends on
    #     kwargs = {dep.key: await dep.func() for dep in self._sense["dependencies"]}
    #     # call the sense function
    #     result = await self._sense["func"](request, **kwargs)

    #     # now call all functions that depended on the sense function - and their dependencies
    #     dependants = self._dependency_graph[self._sense["func"]]
    #     for key, dependant in dependants:
    #         kwargs = await self._resolve(dependant, **{key: result})

    # async def _resolve(self, func):
    #     dependants = self._dependency_graph[self._sense["func"]]
    #     for key, dependant in dependants:
    #         kwargs = await self._resolve_backwards(dependant, **{key: result})

    # async def _resolve_backwards(self, func, **kwargs):
    #     # these are the dependencies of func, we need to resolve them to be able to call func
    #     new_kwargs = {
    #         key: await self._resolve_backwards(dep)
    #         for key, dep in self._dependency_graph[func]
    #     }
    #     return await func(**kwargs, **new_kwargs)

    @classmethod
    def bind_methods(cls, agent):
        bound_methods = {}
        for attr_name in dir(agent):
            attr = getattr(agent, attr_name)
            if inspect.ismethod(attr):
                bound_methods[attr.__func__] = attr

        # bind methods
        routing_methods = []
        for method in bound_methods.values():
            if hasattr(method, "_routing_info"):
                route_info = method._routing_info
                # update to bound method (if it is one)
                route_info["func"] = bound_methods.get(
                    route_info["func"], route_info["func"]
                )
                # also update dependencies to bound methods (if they are)
                for _from in route_info["dependencies"]:
                    _from.func = bound_methods.get(_from.func, _from.func)
                routing_methods.append(method)
        return routing_methods

    @classmethod
    def build_routes(cls, agent):
        # bind decorated functions to the agent
        bound_methods = Route.bind_methods(agent)
        sensor_routes = {}
        actuator_routes = {}
        side_effects = []
        for method in bound_methods:
            route_info = method._routing_info
            if route_info["route"] is None:
                side_effects.append(route_info)
                continue
            if route_info["type"] == "sensor":
                assert route_info["route"] not in sensor_routes
                sensor_routes[route_info["route"]] = route_info
            elif route_info["type"] == "actuator":
                assert route_info["route"] not in actuator_routes
                actuator_routes[route_info["route"]] = route_info
            else:
                raise ValueError(f"Unknown route type: {route_info['type']}")

        # validate keys
        no_output = set(sensor_routes.keys()) - set(actuator_routes.keys())
        if no_output:
            raise ValueError(f"No attempt defined for routes: {list(no_output)}")
        no_input = set(actuator_routes.keys()) - set(sensor_routes.keys())
        if no_input:
            raise ValueError(f"No sense defined for routes: {list(no_input)}")

        # bind the all functions to the agent

        # construct the dependency graph
        dependency_graph = defaultdict(list)

        for info in sensor_routes.values():
            for _from in info["dependencies"]:
                dependency_graph[_from.func].append((_from.key, info["func"]))

        for info in actuator_routes.values():
            for _from in info["dependencies"]:
                dependency_graph[_from.func].append((_from.key, info["func"]))

        for info in side_effects:
            if hasattr(info["func"], "_routing_info"):
                for _from in info["dependencies"]:
                    dependency_graph[_from.func].append((_from.key, info["func"]))
            else:
                # a normal function is not allowed to have dependencies... using `From`
                # TODO maybe we will suppport this at a later date? if we end up needing it
                assert len(From.get_dependencies(info["func"])) == 0

                # we may need to bind the function to the agent

        # build the routes
        for route in sensor_routes.keys():
            _sense_func = sensor_routes[route]
            _attempt_func = actuator_routes[route]
            yield Route(_sense_func, _attempt_func, dependency_graph)

            # self._app.add_api_route(
            #     route,
            #     Route(
            #         _sense_func[0],
            #         _attempt_func[0],
            #     ),
            # )
        # self._app.add_api_route(route_info["route"], attr)

    @classmethod
    def _validate_dependencies(cls, func):
        dependencies = func._routing_info["dependencies"]
        for dep in dependencies:
            dep_info = getattr(dep, "_routing_info", None)
            if dep_info is not None:
                assert (
                    dep_info["type"] == "sensor"
                ), f"Dependency {dep} cannot be of type `attempt`"
                assert (
                    dep_info["route"] is None
                ), f"Dependency {dep} cannot be routed: {dep_info['route']}"
            # otherwise it is just a normal function

    @classmethod
    def _resolve_dependencies(cls, sense, attempt, side_effects):
        # something bad happened... these are internal errors
        assert sense._routing_info["type"] == "sensor"
        assert attempt._routing_info["type"] == "actuator"
        assert sense._routing_info["route"] == attempt._routing_info["route"]
        # user configured the agent wrong if these fail
        Route._validate_dependencies(sense)
        Route._validate_dependencies(attempt)
