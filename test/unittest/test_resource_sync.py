"""Tests for the Resource class synchronous iteration functionality."""

import pytest
from demistar.resource import Resource


class SyncResource(Resource[int, int]):
    """A resource that only implements sync iteration."""

    def __init__(self, values: list[int]):  # noqa
        super().__init__()
        self.values = values
        self.index = 0

    def __enter__(self):
        self.index += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.index = -1

    def get_nowait(self) -> int:  # noqa
        if self.index >= len(self.values):
            raise StopIteration
        val = self.values[self.index]
        self.index += 1
        return val


class TestResourceSync:
    """Test the Resource class synchronous iteration functionality."""

    def test_sync_iteration(self):
        """Test synchronous iteration works correctly."""
        values = [1, 2, 3]
        resource = SyncResource(values)
        # Test __iter__ and __next__
        itered_values = list(resource)
        assert itered_values == values, f"{itered_values} != {values}"

        # Test iteration stops properly
        with pytest.raises(StopIteration):
            next(resource)

        values = [4, 5, 6]
        resource = SyncResource(values)
        # Test __iter__ and __next__
        itered_values = list(resource)
        assert itered_values == values, f"{itered_values} != {values}"

        # Test iteration stops properly
        with pytest.raises(StopIteration):
            next(resource)

    async def test_sync_iteration_with_context(self):
        """Test that stream works correctly."""
        values = [1, 2, 3]
        resource = SyncResource(values)
        result = []
        assert resource.has_context()
        with resource as resource:
            for item in resource:
                result.append(item)
        assert result == values[1:]

    async def test_async_not_implemented(self):
        """Test that async iteration raises NotImplementedError when not implemented."""
        resource = SyncResource([1])

        with pytest.raises(NotImplementedError):
            await resource.__anext__()

        with pytest.raises(NotImplementedError):
            async for _ in resource:
                pass
