"""Resources are the basic building blocks of an environment.

They can be:
- read by sensors
- written to by actuators
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from typing import TYPE_CHECKING, TypeVar, Generic, final
from ..broadcast import BroadcastStream

if TYPE_CHECKING:
    pass
    # from demistar.actuator import Actuator
    # from demistar.sensor import Sensor

T = TypeVar("T")


class Resource(Generic[T]):
    """Base class for all resources."""

    _RESOURCE_API_SYNC = "get_nowait"
    _RESOURCE_API_ASYNC = "get"
    _RESOURCE_API_BROADCAST_STREAM = "_resource_broadcast_stream"

    def __init__(
        self,
        broadcast: bool = False,
        wait_for_listeners: int = 0,
        *args,
        **kwargs,
    ):
        """Constructor.

        Args:
            broadcast (bool): Whether to enable broadcasting of the resource, this is only possible if the resource is async (defines `async get()`).
            wait_for_listeners (int): Number of listeners to wait for before starting to broadcast. Defaults to 0, which will start the broadcast immediately (on call to `broadcast()`).
        """
        super().__init__()
        self._resource_broadcast_stream = None
        # if this wasnt defined in __new__ then we dont need to add it!
        if broadcast and hasattr(self, Resource._RESOURCE_API_ASYNC):
            self._resource_broadcast_stream = BroadcastStream(
                self, wait=wait_for_listeners
            )
        elif broadcast and not hasattr(self, Resource._RESOURCE_API_SYNC):
            raise RuntimeError("Resource is not async, cannot broadcast.")
        self._iterator_in_use = False

    def is_async(self) -> bool:
        """Check if the resource supports asynchronous iteration."""
        return hasattr(self, Resource._RESOURCE_API_ASYNC)

    def is_sync(self) -> bool:
        """Check if the resource supports synchronous iteration."""
        return hasattr(self, Resource._RESOURCE_API_SYNC)

    def is_broadcastable(self) -> bool:
        """Check if the resource is broadcastable (only possible if the resource is also async)."""
        return self._resource_broadcast_stream is not None

    async def broadcast(self) -> BroadcastStream[T]:
        """Call this to start broadcasting the source to any listeners."""
        if not self.is_broadcastable():
            raise RuntimeError("Resource is not broadcastable.")
        return await self._resource_broadcast_stream.broadcast()

    async def __astream__(self) -> AsyncIterator[T]:
        """Return an async iterator for the resource, this is used internally by the resource to iterate over data - it should not be used by listeners of the resource, it may be overriden in a fashion similar to __aiter__ as it was originally intended."""
        try:
            self._iterator_in_use = True
            while True:
                yield await self.__anext__()
        except StopAsyncIteration:
            self._iterator_in_use = False
            # dont reraise, we are returning here!

    def __aiter__(self) -> AsyncIterator[T]:
        """Return an async iterator for the resource.

        If `broadcast = True`, this may be called in multiple places. Each caller is treated as a listener and will receive new data as it arrives. Any data produced before iteration started will not be avaliable to the listener. The broadcast stream must be managed seperately from the listener, typically this will be done via an asyncio task using `broadcast()`.
        """
        try:
            if not self.is_broadcastable():
                if self._iterator_in_use:
                    raise RuntimeError(
                        "Resource is already being asynchronously iterated on, set `broadcast=True` to enable multiple listeners."
                    )
                self._iterator_in_use = True
                return self
            else:
                return self._resource_broadcast_stream.subscribe()
        except StopAsyncIteration:
            self._iterator_in_use = False
            raise

    @final
    def __iter__(self) -> Iterator[T]:
        """Return an iterator for the resource."""
        if self._iterator_in_use:
            raise RuntimeError("Resource is already being asynchronously iterated on.")
        self._iterator_in_use = True
        return self

    @final
    def __next__(self) -> T:
        """Return the next value from the resource synchronously using `get_nowait()`."""
        try:
            return self.get_nowait()
        except StopAsyncIteration:
            self._iterator_in_use = False
            raise
        except AttributeError:
            # check if it is due to `get_nowait`
            if not hasattr(self, Resource._RESOURCE_API_SYNC):
                raise NotImplementedError(
                    "Sync iteration is not implemented for this resource."
                )
            raise

    @final
    async def __anext__(self) -> T:
        """Return the next value from the resource asynchronously using `get()`."""
        try:
            return await self.get()
        except StopAsyncIteration:
            # if we are broadcasting, the iterator is always in use (until __astream__ completes)
            self._iterator_in_use = not self.is_broadcastable()
            raise
        except AttributeError:
            # check if it is due to `get`
            if not hasattr(self, Resource._RESOURCE_API_ASYNC):
                raise NotImplementedError(
                    "Async iteration is not implemented for this resource."
                )
            raise


# if __name__ == "__main__":
#     import pathlib

#
#     sensor = Sensor()  # raw sensor that will attach itself to the resource
