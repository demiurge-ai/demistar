"""Resources are the basic building blocks of an environment.

They can be:
- read by sensors
- written to by actuators
"""

from __future__ import annotations

from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Iterable,
    Generator,
    Iterator,
)

from typing import TYPE_CHECKING, TypeVar, Generic, final
from ..broadcast import BroadcastStream

if TYPE_CHECKING:
    pass
    # from demistar.actuator import Actuator
    # from demistar.sensor import Sensor

S = TypeVar("S")
A = TypeVar("A")


class Resource(Generic[S, A]):
    """Base class for all resources.

    Subclasses should implement the following methods:

    - `get_nowait(self) -> S` for sync read
    - `get(self) -> S` for async read
    - `put(self, item : A)` for async write
    - `put_nowait(self, item : A)` for sync write

    - `__enter__` for context management
    - `__exit__` for context management

    Not all methods need to be implemented, for example, some resources may be read only, or write only.
    """

    _RESOURCE_API_SYNC = "get_nowait"
    _RESOURCE_API_ASYNC = "get"
    _RESOURCE_API_BROADCAST_STREAM = "_resource_broadcast_stream"

    def __init__(
        self,
        broadcast: bool = False,
        wait_for_listeners: int = 0,
        **kwargs,
    ):
        """Constructor.

        Args:
            broadcast (bool): Whether to enable broadcasting of the resource, this is only possible if the resource is async (defines `async get()`).
            wait_for_listeners (int): Number of listeners to wait for before starting to broadcast. Defaults to 0, which will start the broadcast immediately (on call to `broadcast()`).
            kwargs (dict): Additional named arguments.
        """
        super().__init__(**kwargs)
        self._resource_broadcast_stream = None
        # if this wasnt defined in __new__ then we dont need to add it!
        if broadcast:
            self._resource_broadcast_stream = BroadcastStream(
                self, wait=wait_for_listeners
            )
        self._iterator_in_use = False

    def has_context(self) -> bool:
        """Check if the resource supports context management using `with`, if so it should be used."""
        if self.is_async():
            return hasattr(self, "__aenter__") and hasattr(self, "__aexit__")
        elif self.is_sync():
            return hasattr(self, "__enter__") and hasattr(self, "__exit__")
        return False

    def is_async(self) -> bool:
        """Check if the resource supports asynchronous iteration."""
        return hasattr(self, Resource._RESOURCE_API_ASYNC)

    def is_sync(self) -> bool:
        """Check if the resource supports synchronous iteration."""
        return hasattr(self, Resource._RESOURCE_API_SYNC)

    def is_broadcastable(self) -> bool:
        """Check if the resource is broadcastable."""
        return self._resource_broadcast_stream is not None

    async def __aconsume__(
        self, iterator: AsyncIterator[A] | AsyncGenerator[A] | AsyncIterable[A]
    ) -> None:
        async for item in iterator:
            await self.put(item)

    def __consume__(self, iterator: Iterator[A] | Generator[A] | Iterable[A]) -> None:
        for item in iterator:
            self.put_nowait(item)

    async def broadcast(self) -> BroadcastStream[S]:
        """Call this to start broadcasting the source to any listeners.

        TODO give details of what this means in the sync and async case!
        """
        if not self.is_broadcastable():
            raise RuntimeError("Resource is not broadcastable.")
        return await self._resource_broadcast_stream.broadcast()

    async def __astream__(self) -> AsyncIterable[S]:
        """Return an async iterator for the resource, this is used internally by the resource to iterate over data - it should not be used by listeners of the resource, it may be overriden in a fashion similar to __aiter__ as it was originally intended."""
        try:
            self._iterator_in_use = True
            while True:
                yield await self.__anext__()
        except StopAsyncIteration:
            self._iterator_in_use = False
            # dont reraise, we are returning here!

    def __aiter__(self) -> AsyncIterable[S]:
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
    def __iter__(self) -> Iterable[S]:
        """Return an iterator for the resource."""
        if self._iterator_in_use:
            raise RuntimeError("Resource is already being asynchronously iterated on.")
        self._iterator_in_use = True
        return self

    @final
    def __next__(self) -> S:
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
    async def __anext__(self) -> S:
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
