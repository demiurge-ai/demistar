"""TODO document."""

import asyncio
from typing import (
    TypeVar,
)
from collections.abc import (
    AsyncIterator,
    AsyncGenerator,
    Iterator,
    Generator,
)
from .utils.typing import is_async_iter, is_sync_iter
import weakref

T = TypeVar("T")


class BroadcastStream:
    """Broadcast an iterator to multiple listeners.

    Example:
        ```python
        async def source():
            for i in range(10):
                await asyncio.sleep(0.1)
                yield i


        broadcast = BroadcastStream(source())


        async def listener():
            async for item in broadcast.subscribe():
                pass  # do something with the item


        asyncio.gather(broadcast.broadcast(), listener(), listener())
        ```
    """

    STOP_SENTINAL = object()

    def __init__(
        self,
        source: AsyncIterator[T]
        | Iterator[T]
        | AsyncGenerator[T, None]
        | Generator[T, None, None],
        wait: int = 0,
        **kwargs,
    ):
        """Constructor.

        Args:
            source (AsyncGenerator[T, None]): The source to broadcast.
            wait (int, optional): Whether to wait for subscribers to subscribe before broadcasting. Defaults to 0, which means the broadcaster will start broadcasting immediately.
            **kwargs: Additional named arguments.
        """
        self.source = source
        if not (self.is_async() or self.is_sync()):
            raise TypeError(
                f"`source` must be an iterable type, but is: {type(self.source)}"
            )
        self._subscribers: set[asyncio.Queue] = weakref.WeakSet()
        # set when the broadcast is started
        self._is_broadcasting = asyncio.Future()
        # true when the source is done, or the broadcast is cancelled
        self._is_done = False
        # number of subscribers to wait for before starting the broadcast
        self._wait_for = wait
        # condition use to check is required subscribers has been reached
        self._wait_condition = asyncio.Condition() if wait > 0 else None

    def is_sync(self) -> bool:
        """Check if the broadcast source is a synchronous iterable."""
        return is_sync_iter(self.source)

    def is_async(self) -> bool:
        """Check if the broadcast source is a asynchronous iterable."""
        return is_async_iter(self.source)

    def is_broadcasting(self) -> bool:
        """Check if the broadcast is currently broadcasting."""
        return self._is_broadcasting.done()

    def is_ready(self) -> asyncio.Future:
        """Check if the broadcast is ready to be subscribed to."""
        if self._wait_for == 0:
            return self._is_broadcasting
        else:
            ready = asyncio.Future()
            ready.set_result(None)
            return ready

    async def subscribe(self) -> AsyncIterator[T]:
        """Start listening to the broadcast stream."""
        # if the broadcaster is waiting for the first subscriber, wake it up!
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        if self._wait_condition is not None:
            async with self._wait_condition:
                self._wait_condition.notify()
        # wait for the broadcast to start
        await self._is_broadcasting

        try:
            while not self._is_done or not queue.empty():
                item = await queue.get()
                if item is BroadcastStream.STOP_SENTINAL:  # Special signal to stop
                    break
                yield item
        except StopAsyncIteration:
            pass
        finally:
            self._subscribers.discard(queue)

    # def __aiter__(self):
    #     """Call this to start broadcasting the source to any subscribers."""
    #     # use the source as a context manager is it has the methods!

    async def _wait_on_subscribers(self):
        """Used to wait for the N subscribers to subscribe before starting to broadcast."""
        if self._wait_condition is not None:
            async with self._wait_condition:
                await self._wait_condition.wait_for(
                    lambda: len(self._subscribers) >= self._wait_for
                )

    async def broadcast(self):
        """Broadcast the source to any subscribers, this might be prefered over async iteration as it can be used directly in an asyncio.task or in asyncio.gather."""
        # wait for the first subscriber to subscribe before broadcasting
        await self._wait_on_subscribers()
        self._is_broadcasting.set_result(None)
        try:
            if self.is_async():
                return await self._broadcast_async()
            elif self.is_sync():
                return await self._broadcast_sync()
            else:
                raise TypeError("`source` must be AsyncIterable or Iterable")
        finally:
            for queue in self._subscribers:
                await queue.put(BroadcastStream.STOP_SENTINAL)
            self._is_done = True

    def _has_async_context_manager(self) -> bool:
        """Check if the source has a context manager."""
        return hasattr(self.source, "__aenter__") and hasattr(self.source, "__aexit__")

    def _has_sync_context_manager(self) -> bool:
        """Check if the source has a context manager."""
        return hasattr(self.source, "__enter__") and hasattr(self.source, "__exit__")

    async def _broadcast_async(self):
        async for item in self._get_source_aiter(self.source):
            for queue in self._subscribers:
                await queue.put(item)

    # TODO remove, not used
    async def _broadcast_with_async_context_manager(self):
        async with self.source as source:
            async for item in self._get_source_aiter(source):
                for queue in self._subscribers:
                    await queue.put(item)

    def _broadcast_sync(self):
        for item in self.source:
            for queue in self._subscribers:
                queue.put_nowait(item)

    # TODO remove, not used
    def _broadcast_with_sync_context_manager(self):
        with self.source as source:
            for item in source:
                for queue in self._subscribers:
                    queue.put_nowait(item)

    def _get_source_aiter(
        self, source: AsyncIterator[T] | AsyncGenerator[T, None]
    ) -> AsyncIterator[T] | AsyncGenerator[T, None]:
        """We prefer to use __astream__ over __aiter__  to allow __aiter__ to be used by consumers of `source` - rather than having them call a special method for this. See `Resource` for an example."""
        if not hasattr(source, "__aiter__"):
            return source  # the source is probably a generator, just use it as is.
        return getattr(source, "__astream__", source.__aiter__)()
