"""Utility functions for type checking."""

from collections.abc import (
    AsyncIterator,
    AsyncGenerator,
    AsyncIterable,
    Iterator,
    Generator,
    Iterable,
    Callable,
)
from typing import Any
import inspect

__all__ = ["is_sync_iter", "is_async_iter", "is_callable", "is_async_callable"]


def is_callable(source: Any):
    """Check if object is a callable.

    True for:
    - (async) def functions
    - lambda
    - classes that define (async)`__call__`

    Args:
        source (Any): The object to check.

    Returns:
        bool: True if the object is a callable, False otherwise.
    """
    return isinstance(source, Callable)


def is_async_callable(source: Any):
    """Check if object is an async callable.

    True for:
    - async def functions or methods
    - classes that define async `__call__`
    - coroutines

    Args:
        source (Any): The object to check.

    Returns:
        bool: True if the object is an async callable, False otherwise.
    """
    if inspect.iscoroutinefunction(source):
        return True
    return inspect.iscoroutinefunction(getattr(source, "__call__", None))


def is_sync_iter(source: Any) -> bool:
    """Check if the source is a synchronous iterable.

    True for:
    - iterators
    - generators
    - iterables

    Args:
        source (Any): The object to check.

    Returns:
        bool: True if the object is a sync iterable, False otherwise.
    """
    return isinstance(source, Iterator | Generator | Iterable) or inspect.isgenerator(
        source
    )


def is_async_iter(source: Any) -> bool:
    """Check if the source is an asynchronous iterable.

    True for:
    - async iterators
    - async generators
    - async iterables

    Args:
        source (Any): The object to check.

    Returns:
        bool: True if the object is an async iterable, False otherwise.
    """
    # fallback on inspect, sometimes types are not correct... - e.g. <class async_generator> doesnt seem to work well with AsyncGenerator
    return isinstance(
        source, AsyncIterator | AsyncGenerator | AsyncIterable
    ) or inspect.isasyncgen(source)
