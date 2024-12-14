# import pytest
# import asyncio

# from demistar.resource import Resource


# class AsyncResource(Resource[str]):
#     """A resource that only implements async iteration."""

#     def __init__(self, values: list[str]):
#         super().__init__()
#         self.values = values
#         self.index = 0

#     async def get(self) -> str:
#         if self.index >= len(self.values):
#             raise StopAsyncIteration
#         await asyncio.sleep(0.01)  # Simulate async work
#         val = self.values[self.index]
#         self.index += 1
#         return val


# class DualResource(Resource[float]):
#     """A resource that implements both sync and async iteration"""

#     def __init__(self, values: list[float]):
#         super().__init__()
#         self.values = values
#         self.index = 0

#     def get_nowait(self) -> float:
#         if self.index >= len(self.values):
#             raise StopIteration
#         val = self.values[self.index]
#         self.index += 1
#         return val

#     async def get(self) -> float:
#         if self.index >= len(self.values):
#             raise StopAsyncIteration
#         await asyncio.sleep(0.01)
#         val = self.values[self.index]
#         self.index += 1
#         return val


# class EmptyResource(Resource[int]):
#     """A resource that implements neither sync nor async iteration"""

#     pass


# @pytest.mark.asyncio
# class TestResource:
#     def test_sync_iteration(self):
#         """Test synchronous iteration works correctly."""
#         values = [1, 2, 3]
#         resource = SyncResource(values)

#         # Test __iter__ and __next__
#         assert list(resource) == values

#         # Test iteration stops properly
#         with pytest.raises(StopIteration):
#             next(resource)

#     async def test_async_not_implemented(self):
#         """Test that async iteration raises NotImplementedError when not implemented"""
#         resource = SyncResource([1])

#         with pytest.raises(NotImplementedError):
#             await resource.__anext__()

#     async def test_multiple_async_subscribers(self):
#         """Test that multiple subscribers can receive values"""
#         values = ["a", "b", "c"]
#         resource = AsyncResource(values)

#         async def collect_values():
#             collected = []
#             async for val in resource:
#                 collected.append(val)
#             return collected

#         # Create two subscribers
#         task1 = asyncio.create_task(collect_values())
#         task2 = asyncio.create_task(collect_values())

#         results = await asyncio.gather(task1, task2)

#         assert results[0] == values
#         assert results[1] == values

#     def test_empty_resource(self):
#         """Test that a resource without any iteration methods raises appropriate errors"""
#         resource = EmptyResource()

#         with pytest.raises(NotImplementedError):
#             next(resource)

#         with pytest.raises(NotImplementedError):
#             for _ in resource:
#                 pass

#     async def test_dual_resource(self):
#         """Test a resource that implements both sync and async iteration"""
#         values = [1.0, 2.0, 3.0]
#         resource = DualResource(values)

#         # Test sync iteration
#         assert list(resource) == values

#         # Reset index
#         resource.index = 0

#         # Test async iteration
#         collected = []
#         async for val in resource:
#             collected.append(val)

#         assert collected == values

#     async def test_broadcast_cleanup(self):
#         """Test that broadcast resources are properly cleaned up"""
#         values = ["a", "b", "c"]
#         resource = AsyncResource(values)

#         # Create and immediately exit a subscriber
#         async for _ in resource:
#             break

#         # Verify we can still create new subscribers
#         collected = []
#         async for val in resource:
#             collected.append(val)

#         assert collected == values
