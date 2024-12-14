"""Sensors are components that can read/receive data from a resource."""

from __future__ import annotations

import asyncio
import ray

from typing import Any
from .resource import Resource
from .component import Component
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent


class Sensor(Component):
    def __init__(self, resource: Resource, *args, **kwargs):
        super().__init__()
        self._resource = resource
        self._buffer = asyncio.Queue()
        self._agent = None  # set on `attach`
        self._buffer_aiter = None
        self._buffer_iter = None

        # attach self to the resource, the resource will call "put"
        self._resource.attach(self)

    def __put__(self, item: Any):
        """Used internally by the resource to add new observations to the sensors buffer."""
        try:
            self._buffer.put_nowait(item)
        except asyncio.QueueFull:
            raise ValueError("Sensor buffer is full, cannot add new item.")

    def __iter__(self):
        if self._buffer_iter:
            raise ValueError("Observations are already being consumed synchronously.")
        self._buffer_iter = _ObservationsIter(self._buffer)
        return self._buffer_iter

    def __aiter__(self):
        if self._buffer_aiter:
            raise ValueError("Observations are already being consumed asynchronously.")
        self._buffer_aiter = _ObservationsAsyncIter(self._buffer)
        return self._buffer_aiter

    def __len__(self):  # noqa
        return self._buffer.qsize()

    def is_empty(self):
        """Checks if this `_Observations` is empty.

        Returns:
            bool: True if this `_Observations` is empty, False otherwise.
        """
        return self._buffer.empty()

    def detach(self, agent: Agent):
        super().detach(agent)
        self.cancel()

    def cancel(self):
        if self._buffer_aiter:
            self._buffer_aiter.cancel()


class _ObservationsIter:
    def __init__(self, buffer: asyncio.Queue):
        self._buffer = buffer

    def __next__(self) -> Any:
        """Get the next event from this observation, this is a blocking call."""
        try:
            item = self._buffer.get_nowait()
        except asyncio.QueueEmpty:
            raise StopIteration
        return ray.get(item) if isinstance(item, ray.ObjectRef) else item


class _ObservationsAsyncIter:
    SENTINEL = object()

    def __init__(self, buffer: asyncio.Queue):
        """Constructor.

        Args:
            buffer (asyncio.Queue): buffer to consume asynchronously.
        """
        self._buffer = buffer

    async def __anext__(self) -> Any:
        """Asynchronously get the next observation."""
        item = await self._buffer.get()
        if item is _ObservationsAsyncIter.SENTINEL:
            raise StopAsyncIteration
        return await ray.get(item) if isinstance(item, ray.ObjectRef) else item

    def cancel(self):
        """Cancel the async iteration."""
        self._buffer.put_nowait(_ObservationsAsyncIter.SENTINEL)
