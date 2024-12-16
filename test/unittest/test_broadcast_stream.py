"""Test the BroadcastStream class."""

import pytest
import asyncio
from demistar.broadcast import BroadcastStream


@pytest.mark.timeout(2)
@pytest.mark.asyncio(loop_scope="function")
class TestBroadcastStream:
    """Test the BroadcastStream class."""

    async def test_broadcast_without_wait(self):
        """Test broadcasting without waiting for subscribers - check for possible hang."""
        values = [1, 2, 3]

        async def source():
            for x in values:
                yield x

        broadcast = BroadcastStream(source(), wait=0)

        async def listen():
            results = []
            async for item in broadcast.subscribe():
                results.append(item)
            # print(results) # this could be any number of values...

        await asyncio.gather(broadcast.broadcast(), listen())

    async def test_listen_after_broadcast(self):
        """Test listening after broadcasting has finished."""
        values = [1, 2, 3]

        async def source():
            for x in values:
                yield x

        # NOTE: if wait > 0 then the broadcast will wait for a subscriber indefinitely...
        broadcast = BroadcastStream(source(), wait=0)

        async def listen():
            async for _ in broadcast.subscribe():
                pass

        await asyncio.gather(broadcast.broadcast())
        await asyncio.gather(listen())

    # async def test_multiple_subscribers(self):
    #     """Test multiple subscribers receive the same data."""

    #     async def source():
    #         for i in range(5):
    #             await asyncio.sleep(0.01)  # Simulate real async work
    #             yield i

    #     broadcast = BroadcastStream(source())

    #     async def collect():
    #         results = []
    #         async for item in broadcast.subscribe():
    #             results.append(item)
    #         return results

    #     # Start multiple subscribers
    #     results = await asyncio.gather(collect(), collect(), collect())

    #     # All subscribers should get the same data
    #     assert all(r == results[0] for r in results)

    # async def test_late_subscriber(self):
    #     """Test that late subscribers only get new data."""

    #     async def source():
    #         for i in range(5):
    #             await asyncio.sleep(0.01)
    #             yield i

    #     broadcast = BroadcastStream(source())

    #     # First subscriber
    #     early_results = []
    #     late_results = []

    #     async def early_subscriber():
    #         async for item in broadcast.subscribe():
    #             early_results.append(item)
    #             if item == 2:  # Add late subscriber after receiving 3 items
    #                 asyncio.create_task(late_subscriber())

    #     async def late_subscriber():
    #         async for item in broadcast.subscribe():
    #             late_results.append(item)

    #     await early_subscriber()

    #     assert early_results == [0, 1, 2, 3, 4]
    #     assert late_results == [3, 4]  # Late subscriber only gets newer items

    # async def test_wait_for_subscribers(self):
    #     """Test waiting for subscribers before broadcasting."""

    #     async def source():
    #         yield "data"

    #     broadcast = BroadcastStream(source(), wait=2)  # Wait for 2 subscribers

    #     async def subscriber():
    #         async for _ in broadcast.subscribe():
    #             return "received"

    #     # Start broadcast but don't wait
    #     broadcast_task = asyncio.create_task(broadcast.broadcast())

    #     # Add first subscriber - shouldn't receive data yet
    #     sub1 = asyncio.create_task(subscriber())
    #     await asyncio.sleep(0.01)
    #     assert not sub1.done()

    #     # Add second subscriber - now both should receive data
    #     sub2 = asyncio.create_task(subscriber())
    #     results = await asyncio.gather(sub1, sub2)
    #     assert results == ["received", "received"]

    #     await broadcast_task

    # async def test_cleanup(self):
    #     """Test proper cleanup of subscribers."""

    #     async def source():
    #         for i in range(100):
    #             yield i

    #     broadcast = BroadcastStream(source())

    #     async def subscriber():
    #         async for item in broadcast.subscribe():
    #             if item >= 5:
    #                 break

    #     # Start multiple subscribers that exit early
    #     await asyncio.gather(subscriber(), subscriber())

    #     # Verify subscribers were removed
    #     assert len(broadcast._subscribers) == 0

    # async def test_error_handling(self):
    #     """Test error handling in broadcast stream."""

    #     async def faulty_source():
    #         yield 1
    #         raise ValueError("Test error")

    #     broadcast = BroadcastStream(faulty_source())

    #     with pytest.raises(ValueError, match="Test error"):
    #         async for _ in broadcast.subscribe():
    #             pass

    # async def test_context_manager(self):
    #     """Test using broadcast stream with async context manager."""

    #     class ContextSource:
    #         async def __aenter__(self):
    #             self.value = 0
    #             return self

    #         async def __aexit__(self, exc_type, exc_val, exc_tb):
    #             self.value = None

    #         async def __aiter__(self):
    #             while self.value < 3:
    #                 yield self.value
    #                 self.value += 1

    #     source = ContextSource()
    #     broadcast = BroadcastStream(source)
