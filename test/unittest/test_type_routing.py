import unittest
from typing import List, Dict, Tuple, Any
from star_ray.agent.component.type_routing import _TypeRouter, observe, resolve_first_argument_types


class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass


class E:
    pass


class TestTypeRouting(unittest.TestCase):

    def test_resolve_types(self):
        result = _TypeRouter.resolve_route_types(
            [list, List, Dict[str, Any], Tuple, Any, int | str])
        self.assertListEqual(result, [list, list, dict, tuple, Any, int, str])

    def test_resolve_first_argument_types(self):
        def myfunc1(self, x: List[str], y: object, z: int, w: Any) -> float:
            pass

        def myfunc2(x: str, y: object, z: int, w: Any) -> float:
            pass
        TypeAlias = str | int | List[str]

        def myfunc3(x: TypeAlias) -> float:
            pass
        result = resolve_first_argument_types(myfunc1)
        self.assertListEqual(result, [list])
        result = resolve_first_argument_types(myfunc2)
        self.assertListEqual(result, [str])
        result = resolve_first_argument_types(myfunc3)
        self.assertListEqual(result, [str, int, list])

    def test_observe_type_routing(self):
        # Define observe-decorated functions
        @observe([A])
        def func_a(e):
            return f"func_a: {type(e).__name__}"

        @observe([C])
        def func_c(e):
            return f"func_c: {type(e).__name__}"

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(func_a)
        router.add(func_c)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A"])
        self.assertEqual(router(B()), ["func_a: B"])
        self.assertEqual(router(C()), ["func_c: C"])
        self.assertEqual(router(D()), ["func_c: D"])
        self.assertEqual(router(E()), [])

    def test_observe_type_routing_with_typehints(self):

        @observe
        def func_a(e: A):
            return f"func_a: {type(e).__name__}"

        @observe
        def func_ab(e: A | B):
            return f"func_ab: {type(e).__name__}"

        # Initialize TypeRouter
        router = _TypeRouter()
        router.add(func_a)
        router.add(func_ab)

        # Test routing for various types
        self.assertEqual(router(A()), ["func_a: A", "func_ab: A"])
        # func_a will not be called because a function for B was found!
        self.assertEqual(router(B()), ["func_ab: B"])
        self.assertEqual(router(E()), [])


if __name__ == "__main__":
    unittest.main()
