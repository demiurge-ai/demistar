import unittest
import asyncio
from demistar.agent.dag import ComputeGraph, ComputeGraphHalt


# Example async functions for testing
async def func_a():  # noqa
    return "A"


async def func_b(a):  # noqa
    return f"B({a})"


async def func_c(a):  # noqa
    return f"C({a})"


async def func_d(b, c):  # noqa
    return f"D({b}, {c})"


async def func_fail():
    raise ComputeGraphHalt()


class TestComputeGraph(unittest.TestCase):
    """Test the ComputeGraph class."""

    def setUp(self):
        """Set up the test case."""
        self.graph = ComputeGraph()

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        self.graph.add_edge(func_a, "a", func_b)
        self.assertIn((func_a, func_b), self.graph._graph.edges)

    def test_cycle_detection(self):
        """Test cycle detection."""
        self.graph.add_edge(func_a, "a", func_b)
        with self.assertRaises(ValueError):
            self.graph.add_edge(func_b, "b", func_a)  # This should create a cycle

    def test_run_graph(self):
        """Test running the graph."""
        self.graph.add_edge(func_a, "a", func_b)
        self.graph.add_edge(func_a, "a", func_c)
        self.graph.add_edge(func_b, "b", func_d)
        self.graph.add_edge(func_c, "c", func_d)

        async def run_test():
            results = {}
            async for func, result in self.graph.run({}):
                results[func] = result

            self.assertEqual(results[func_a], "A")
            self.assertEqual(results[func_b], "B(A)")
            self.assertEqual(results[func_c], "C(A)")
            self.assertEqual(results[func_d], "D(B(A), C(A))")

        asyncio.run(run_test())

    def test_run_and_halt_graph(self):
        """Test halting of one line of the graph the graph."""
        self.graph.add_edge(func_fail, "a", func_b)
        self.graph.add_edge(func_a, "a", func_c)

        async def run_test():
            results = {}
            async for func, result in self.graph.run({}):
                results[func] = result
            self.assertEqual(results[func_a], "A")
            self.assertEqual(results[func_b], None)
            self.assertEqual(results[func_c], "C(A)")
            self.assertEqual(results[func_fail], None)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
