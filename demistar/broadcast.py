import asyncio
from typing import AsyncGenerator, Set, TypeVar, AsyncIterator
import weakref

T = TypeVar("T")


class BroadcastStream:
    """Broadcast an async iterator to multiple listeners.

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

    def __init__(
        self,
        source: AsyncGenerator[T, None],
        *args,
        wait: int = 0,
        **kwargs,
    ):
        """Constructor.

        Args:
            source (AsyncGenerator[T, None]): The source to broadcast.
            wait (int, optional): Whether to wait for subscribers to subscribe before broadcasting. Defaults to 0, which means the broadcaster will start broadcasting immediately.
        """
        self.source = source
        self._subscribers: set[asyncio.Queue] = weakref.WeakSet()
        # set when the broadcast is started
        self._is_broadcasting = asyncio.Future()
        # true when the source is done, or the broadcast is cancelled
        self._is_done = False
        # number of subscribers to wait for before starting the broadcast
        self._wait_for = wait
        # condition use to check is required subscribers has been reached
        self._wait_condition = asyncio.Condition() if wait > 0 else None

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
                if item is StopAsyncIteration:  # Special signal to stop
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
            if hasattr(self.source, "__aenter__") and hasattr(self.source, "__aexit__"):
                return await self._broadcast_with_async_context_manager()
            elif hasattr(self.source, "__enter__") and hasattr(self.source, "__exit__"):
                return await self._broadcast_with_sync_context_manager()
            else:
                return await self._broadcast()
        finally:
            for queue in self._subscribers:
                await queue.put(StopAsyncIteration)
            self._is_done = True

    async def _broadcast(self):
        async for item in self._get_source_aiter(self.source):
            for queue in self._subscribers:
                await queue.put(item)

    async def _broadcast_with_async_context_manager(self):
        async with self.source as source:
            async for item in self._get_source_aiter(source):
                for queue in self._subscribers:
                    await queue.put(item)

    async def _broadcast_with_sync_context_manager(self):
        # TODO the return of __enter__ is not used?
        async with self.source as source:
            async for item in self._get_source_aiter(source):
                for queue in self._subscribers:
                    await queue.put(item)

    def _get_source_aiter(self, source: AsyncIterator[T]) -> AsyncIterator[T]:
        """We prefer to use __astream__ over __iter__  to allow __aiter__ be used by consumers of `source` - rather than having them call a special method for this. See `Resource` for an example of this."""
        return getattr(source, "__astream__", source.__aiter__)()
