"""Tests for the Resource class asynchronous iteration functionality."""

import pytest
import asyncio

from demistar.resource import Resource


class AsyncResource(Resource[int, int]):
    """A resource that only implements async iteration."""

    def __init__(self, values: list[int], **kwargs):  # noqa
        super().__init__(**kwargs)
        self.values = values
        self.index = 0

    async def __aenter__(self):
        self.index += 1
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.index = -1

    async def get(self) -> int:  # noqa
        if self.index >= len(self.values):
            raise StopAsyncIteration()
        await asyncio.sleep(0)  # Simulate async work
        val = self.values[self.index]
        self.index += 1
        return val


@pytest.mark.timeout(2)
@pytest.mark.asyncio
class TestResourceAsync:
    """Tests for the Resource class asynchronous iteration functionality."""

    async def test_sync_not_implemented(self):
        """Test that sync iteration raises NotImplementedError when not implemented."""
        resource = AsyncResource([1])

        with pytest.raises(NotImplementedError):
            next(resource)

        with pytest.raises(NotImplementedError):
            for _ in resource:
                pass

    async def test_async_iteration_single(self):
        """Test that async iteration works correctly."""
        values = [1, 2, 3]
        resource = AsyncResource(values)

        # a single listener can use the resource async directly - but no others should be able to!
        aiter_values = []
        async for val in resource:
            aiter_values.append(val)

        assert aiter_values == values

    async def test_async_iterator_with_context(self):
        """Test that async stream works correctly - context manager is used."""
        values = [1, 2, 3]
        resource = AsyncResource(values)

        # a single listener can use the resource async directly - but no others should be able to!
        aiter_values = []
        assert resource.has_context()
        async with resource as resource:
            async for val in resource:
                aiter_values.append(val)

        assert aiter_values == values[1:]

    async def test_async_broadcast_error(self):
        """Test that an error is raised when trying to iterate asynchronously on a non-broadcastable resource."""
        resource = AsyncResource([1])

        async def _listen():
            async for val in resource:
                pass

        with pytest.raises(RuntimeError):
            await asyncio.gather(*[_listen() for _ in range(2)])

    async def test_async_broadcast_multiple(self):
        """Test that multiple listeners can use the resource async directly - but no others should be able to!"""
        values = [1, 2, 3]
        n = 2
        resource = AsyncResource(values, broadcast=True, wait_for_listeners=n)

        async def _listen():
            result = []
            async for val in resource:
                result.append(val)
            # the context manager is used automatically by broadcast!
            assert result == values

        # NOTE: broadcast doesnt use the context manager automatically!
        await asyncio.gather(resource.broadcast(), *[_listen() for _ in range(n)])
