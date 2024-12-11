import unittest
import asyncio
from demistar.agent.dag import ComputeGraph


# Example async functions for testing
async def func_a():  # noqa
    await asyncio.sleep(0.1)
    return "A"


async def func_b(a):  # noqa
    await asyncio.sleep(0.1)
    return f"B({a})"


async def func_c(a):  # noqa
    await asyncio.sleep(0.1)
    return f"C({a})"


async def func_d(b, c):  # noqa
    await asyncio.sleep(0.1)
    return f"D({b}, {c})"


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


if __name__ == "__main__":
    unittest.main()
