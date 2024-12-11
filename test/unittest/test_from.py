import unittest
import asyncio
from demistar.agent.dag import From, ComputeGraph


# Example async functions for testing
async def func_A() -> str:  # noqa
    return "A"


async def func_B(a: str = From(func_A)) -> str:  # noqa
    return f"B({a})"


async def func_C(a: str = From(func_A), b: str = From(func_B)) -> str:  # noqa
    return f"C({a}, {b})"


class TestFrom(unittest.TestCase):
    """Test the use of From for dependency injection."""

    def test_resolve_dependencies(self):
        """Test the resolve_dependencies method."""
        dependencies = From.resolve_dependencies(func_B)
        self.assertIn("a", dependencies)
        self.assertIsInstance(dependencies["a"], From)
        self.assertEqual(dependencies["a"]._func, func_A)

        dependencies = From.resolve_dependencies(func_C)
        self.assertIn("a", dependencies)
        self.assertIsInstance(dependencies["a"], From)
        self.assertEqual(dependencies["a"]._func, func_A)
        self.assertIn("b", dependencies)
        self.assertIsInstance(dependencies["b"], From)
        self.assertEqual(dependencies["b"]._func, func_B)

    def test_build_for_function(self):
        """Test building from a function."""
        graph = From.build(func_C)
        self.assertIsInstance(graph, ComputeGraph)
        self.assertIn((func_A, func_B), graph._graph.edges)
        self.assertIn((func_A, func_C), graph._graph.edges)
        self.assertIn((func_B, func_C), graph._graph.edges)

        # run the graph to make sure there are not obvious problems...
        # an actual test of the DAG graph computation is done in test_dag.py
        async def _run():
            async for _ in graph.run():
                pass

        asyncio.run(_run())

    def test_build_for_instance(self):
        """Test building from an instance."""

        class TestClass:
            # func_A is defined outside the class
            async def func_B(self, a: str = From(func_A)) -> str:  # noqa
                return f"B({a})"

            async def func_C(self, a: str, b: str = From(func_B)) -> str:  # noqa
                return f"C({a}, {b})"

            async def func_D(self, b: str = From(func_B), c: str = From(func_C)) -> str:  # noqa
                return f"D({b}, {c})"

        instance = TestClass()
        graph = From.build(instance)
        self.assertIsInstance(graph, ComputeGraph)
        self.assertIn((func_A, instance.func_B), graph._graph.edges)
        self.assertIn((instance.func_B, instance.func_C), graph._graph.edges)
        self.assertIn((instance.func_B, instance.func_D), graph._graph.edges)
        self.assertIn((instance.func_C, instance.func_D), graph._graph.edges)

        # run the graph to make sure there are not obvious problems...
        # an actual test of the DAG graph computation is done in test_dag.py
        async def _run():
            async for _ in graph.run(initial_args={instance.func_C: {"a": "A"}}):
                pass

        asyncio.run(_run())

    def test_multi_dependency(self):
        i = 0

        async def func_N() -> int:
            nonlocal i
            i += 1
            return i

        # n should be the same as for func_S
        async def func_T(n: int = From(func_N)) -> int:
            return n

        # n should be the same as for func_T
        async def func_S(n: int = From(func_N)) -> int:
            return n

        async def func_ST(s: int = From(func_S), t: int = From(func_T)) -> int:
            return s + t

        async def run(n):
            graph = From.build(func_ST)
            results = {}
            async for func, result in graph.run({}):
                results[func] = result
            self.assertEqual(results[func_ST], n)

        async def run_test():
            await run(2)
            await run(4)

        asyncio.run(run_test())

    def test_no_dependencies(self):
        """Test that an error is raised if no dependencies are found."""

        async def func_D() -> str:
            return "D"

        with self.assertRaises(ValueError):
            From.build(func_D)


if __name__ == "__main__":
    unittest.main()
