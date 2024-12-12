import ray
import asyncio

from ...event import Event


class _Observations:
    """Unified class for managing collections of observations, both local and remote."""

    def __init__(self, objects: list[Event | ray.ObjectRef] = ()):
        """Constructor.

        Args:
            objects (list[Event  |  ray.ObjectRef], optional): list of events or object refs to push into this `_Observations`. Defaults to [].
        """
        self._queue = asyncio.Queue()
        self.push_all(objects)

        self._queue_aiter = None

    def __len__(self):
        return self._queue.qsize()

    def is_active(self):
        """Checks if this `_Observations` is being consumed asynchronously.

        Returns:
            bool: True if this `_Observations` is being consumed asynchronously, False otherwise.
        """
        return self._queue_aiter is not None

    def is_empty(self):
        """Checks if this `_Observations` is empty.

        Returns:
            bool: True if this `_Observations` is empty, False otherwise.
        """
        return self._queue.empty()

    def push_all(self, events: list[Event | ray.ObjectRef]) -> None:
        """Pushes a list of events into this `_Observations`.

        Args:
            events (list[Event  |  ray.ObjectRef]): list of events to push into this `_Observations`.
        """
        for event in filter(None, events):
            self._queue.put_nowait(event)

    def push(self, event: Event | ray.ObjectRef) -> None:
        """Pushes a single event into this `_Observations`.

        Args:
            event (Event | ray.ObjectRef): event to push into this `_Observations`.
        """
        if event:
            self._queue.put_nowait(event)

    def pop(self) -> Event:
        """Pops the most recent event from this `_Observations`.

        Returns:
            Event: event popped from this `_Observations`.
        """
        if self._queue_aiter:
            raise ValueError("Observations are already being consumed asynchronously.")
        item = self._queue.get_nowait()  # raises an error if the queue is empty
        return ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def __iter__(self):
        return self

    def __next__(self) -> Event:
        """Get the next event from this observation, this is a blocking call."""
        if self._queue_aiter:
            raise ValueError("Observations are already being consumed asynchronously.")
        if self._queue.empty():
            raise StopIteration
        item = self._queue.get_nowait()
        return ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def __aiter__(self):
        if self._queue_aiter:
            raise ValueError("Observations are already being consumed asynchronously.")
        # just a placeholder to prevent calling __aiter__ again
        self._queue_aiter = _ObservationsAsyncIter(self)
        return self._queue_aiter

    def cancel(self):
        if self._queue_aiter:
            self._queue_aiter.cancel()


class _ObservationsAsyncIter:
    SENTINEL = object()

    def __init__(self, observations: _Observations):
        """Constructor.

        Args:
            observations (Observations): observations to consume asynchronously.
        """
        self._observations = observations

    async def __anext__(self) -> Event:
        """Asynchronously get the next event."""
        item = await self._observations._queue.get()
        if item is _ObservationsAsyncIter.SENTINEL:
            raise StopAsyncIteration
        return await ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def cancel(self):
        """Cancel the async iteration."""
        self._observations._queue.put_nowait(_ObservationsAsyncIter.SENTINEL)
