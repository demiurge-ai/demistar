"""DAG for computing functions in a pipeline."""

from typing import Callable, Any  # noqa: UP035
import asyncio
import networkx as nx
import io


class ComputeGraphHalt(Exception):
    """This will signal the compute graph that the current node failed in its execution, any nodes that depend on the failing node will not be executed.

    This can be used to manage dynamic dependencies - e.g. if a node is removed during the computation.
    """


class ComputeGraph:
    """A DAG for computing functions (or other objects) that depend on each other in a pipeline."""

    def __init__(self):
        """Construct a new compute graph."""
        super().__init__()
        self._graph = nx.DiGraph()

    def is_empty(self) -> bool:
        """Is the graph empty?

        Returns:
            bool: True if the graph is empty, False otherwise.
        """
        return len(self._graph.nodes) == 0

    def replace_node(self, old: Any, new: Any):
        """Replace a node in the graph with a new node.

        Args:
            old (Any): The old node to replace.
            new (Any): The new node.

        Raises:
            ValueError: If the old node does not exist in the graph.
        """
        if old not in self._graph:
            raise ValueError(f"Node {old} does not exist in the graph.")

        # Get the attributes and edges of the old node
        node_attributes = self._graph.nodes[old]
        edges = list(self._graph.edges(old, data=True))

        # Remove the old node
        self._graph.remove_node(old)

        # Add the new node with the same attributes
        self._graph.add_node(new, **node_attributes)

        # Re-add the edges to the new node
        for _, neighbor, edge_attributes in edges:
            self._graph.add_edge(new, neighbor, **edge_attributes)

    def add_edge(self, func1: Any, arg_name: str, func2: Any):
        """Add an edge to the graph.

        Args:
            func1 (Any): The dependency.
            arg_name (str): The name of the func2 argument that func1 returns.
            func2 (Any): The object that depends on func1.
        """
        # self._check_async(func1)
        # self._check_async(func2)
        if (func1, func2) in self._graph.edges:
            raise ValueError(f"Edge from {func1} to {func2} already exists")
        self._graph.add_edge(func1, func2, arg_name=arg_name)

        # Check for cycles
        if nx.has_path(self._graph, func2, func1):
            # If a path exists from func2->func1, adding the edge created a cycle
            self._graph.remove_edge(func1, func2)
            raise ValueError(
                f"Edge from {func1} to {func2} creates a cycle, the compute graph must be a DAG."
            )

    def _check_async(self, func: Any):
        """Check that a function is async."""
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"Function {func} must be async")

    async def _execute(self, func: Any, args: dict[str, Any]) -> Any:
        """Execute a function with the given arguments."""
        # by default assume that we are dealing with a coroutine function
        return await func(**args)

    # Define a function to execute the graph
    async def run(self, initial_args: dict[Callable, dict[str, Any]] | None = None):
        """Run the compute graph.

        Args:
            initial_args (dict[Callable, dict[str, Any]] | None): The initial named arguments for the graph.
        """
        if initial_args is None:
            initial_args = {}
        futures = {func: asyncio.Future() for func in self._graph.nodes}

        async def execute_node(func):
            # Gather arguments for the current function
            try:
                args = {
                    self._graph.edges[predecessor, func]["arg_name"]: await futures[
                        predecessor
                    ]
                    for predecessor in self._graph.predecessors(func)
                }
                # Add any initial arguments
                args.update(initial_args.get(func, {}))
                # Execute the function and store the result
                result = await self._execute(func, args)
            except ComputeGraphHalt:
                # Set the result in the future, this will cascade of stop compute
                futures[func].set_exception(ComputeGraphHalt())
                return func, None  # this is ok
            except Exception as e:
                futures[func].set_exception(ComputeGraphHalt())
                raise e
            # Set the result in the future
            futures[func].set_result(result)
            return func, result

        # Create tasks for all nodes
        tasks = {
            func: asyncio.create_task(execute_node(func))
            for func in nx.topological_sort(self._graph)
        }

        pending = set(tasks.values())
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                func, result = task.result()
                try:
                    # this will return immediately since the task is already done.
                    # needs to be explicitly awaited, this could be done in execute_node ! <- TODO
                    await futures[func]
                except ComputeGraphHalt:
                    pass  # the compute graph was halted for this node
                yield func, result

    def __repr__(self):  # noqa
        return str(self)

    def __str__(self):  # noqa
        if self.is_empty():
            return "DAG()"
        result = io.StringIO()
        result.write("DAG(\n")
        for edge in self._graph.edges:
            fqn1 = f"{edge[0].__module__}.{edge[0].__qualname__}"
            fqn2 = f"{edge[1].__module__}.{edge[1].__qualname__}"
            result.write(
                f"  {fqn1} -({self._graph.edges[edge]['arg_name']})-> {fqn2}\n"
            )
        result.write(")")
        return result.getvalue()
