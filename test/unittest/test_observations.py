import unittest
from unittest.mock import MagicMock, patch
import asyncio
from demistar.agent._observations import _Observations
from demistar.event import Event


class TestObservations(unittest.TestCase):
    def setUp(self):  # noqa
        # Mock Event and ray.ObjectRef
        self.event1 = MagicMock(spec=Event)
        self.event2 = MagicMock(spec=Event)
        self.object_ref1 = MagicMock()
        self.object_ref2 = MagicMock()

        # Mock ray.get to return the mocked events
        self.object_ref1.get = MagicMock(return_value=self.event1)
        self.object_ref2.get = MagicMock(return_value=self.event2)

    def test_empty(self):
        """Test the empty method of the _Observations class."""
        obs = _Observations.empty()
        self.assertTrue(obs.is_empty())

    def test_push_and_pop(self):
        """Test the push and pop methods of the _Observations class."""
        obs = _Observations([self.event1])
        obs.push(self.event2)
        self.assertEqual(len(obs), 2)
        self.assertEqual(obs.pop(), self.event1)
        self.assertEqual(obs.pop(), self.event2)
        self.assertTrue(obs.is_empty())

    def test_push_all(self):
        """Test the push_all method of the _Observations class."""
        obs = _Observations([])
        obs.push_all([self.event1, self.event2])
        self.assertEqual(len(obs), 2)
        self.assertEqual(obs.pop(), self.event1)
        self.assertEqual(obs.pop(), self.event2)

    def test_iter(self):
        """Test the iteration of the _Observations class."""
        obs = _Observations([self.event1, self.event2])
        iter_obs = iter(obs)
        self.assertEqual(next(iter_obs), self.event1)
        self.assertEqual(next(iter_obs), self.event2)
        with self.assertRaises(StopIteration):
            next(iter_obs)
        # iterating will always consume the observations!
        self.assertTrue(obs.is_empty())

    def test_async_iteration(self):
        """Test the async iteration of the _Observations class."""
        obs = _Observations()

        async def _test_async_iter():
            count = 0
            async for item in obs:
                self.assertIn(item, [self.event1, self.event2])
                count += 1
            self.assertEqual(count, 2)

        async def push_events():
            obs.push(self.event1)
            obs.push(self.event2)
            obs.close()

        async def main():
            await asyncio.gather(_test_async_iter(), push_events())

        asyncio.run(main())

    def test_async_iteration_pop(self):
        """Test the async iteration of the _Observations class."""
        obs = _Observations()

        async def _test_async_iter():
            async for item in obs:
                self.assertIn(item, [self.event1, self.event2])
                with self.assertRaises(ValueError):
                    obs.pop()  # cannot do this while consuming async!

        async def push_events():
            obs.push(self.event1)
            obs.push(self.event2)
            obs.close()

        async def main():
            await asyncio.gather(_test_async_iter(), push_events())

        asyncio.run(main())


if __name__ == "__main__":
    unittest.main()
