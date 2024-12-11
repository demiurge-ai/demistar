import ray
import asyncio

from ..event import Event


class _Observations:
    """Unified class for managing collections of observations, both local and remote."""

    def __init__(self, objects: list[Event | ray.ObjectRef] = ()):
        self._queue = asyncio.Queue()
        for obj in objects:
            self._queue.put_nowait(obj)
        self._async_mode = False
        self._closed = False

    def __len__(self):
        return self._queue.qsize()

    def is_empty(self):
        return self._queue.empty()

    def push_all(self, items: list[Event | ray.ObjectRef]) -> None:
        for item in filter(None, items):
            self._queue.put_nowait(item)

    def push(self, item: Event | ray.ObjectRef) -> None:
        if item:
            self._queue.put_nowait(item)

    def pop(self) -> Event:
        if self._queue.empty():
            raise IndexError("Observations queue is empty.")
        if self._async_mode:
            raise ValueError("Observations are already being consumed asynchronously.")
        item = self._queue.get_nowait()
        return ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def __iter__(self):
        return self

    def __next__(self) -> Event:
        if self._async_mode:
            raise ValueError("Observations are already being consumed asynchronously.")
        if self._queue.empty():
            raise StopIteration
        item = self._queue.get_nowait()
        return ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def __aiter__(self):
        if self._async_mode:
            raise ValueError("Observations are already being consumed asynchronously.")
        self._async_mode = True
        return self

    async def __anext__(self) -> Event:
        item = await self._queue.get()
        if item is None:
            raise StopAsyncIteration
        return await ray.get(item) if isinstance(item, ray.ObjectRef) else item

    @classmethod
    def empty(cls):
        return _Observations([])

    def close(self):
        self._closed = True
        if self._async_mode:
            # sentinal to indicate that the queue has been closed and any async iteration should stop.
            self._queue.put_nowait(None)
