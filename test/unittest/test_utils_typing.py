"""Test the typing utils."""

import pytest
import asyncio

from demistar.utils.typing import (
    is_async_callable,
    is_callable,
    is_async_iter,
    is_sync_iter,
)


async def async_func():  # noqa
    pass


def sync_func():  # noqa
    pass


class AsyncCallable:  # noqa
    async def __call__(self):  # noqa
        pass


class SyncCallable:  # noqa
    def __call__(self):  # noqa
        pass


def sync_gen():  # noqa
    yield from range(3)


async def async_gen():  # noqa
    async for _ in range(3):
        asyncio.sleep(0)
        yield _


async def coroutine_gen():  # noqa
    for x in range(3):
        yield x


def async_gen_expr():  # noqa
    return (x async for x in async_gen())


def sync_gen_expr():  # noqa
    return (x for x in range(3))


class SyncIterable:  # noqa
    def __iter__(self):
        return iter([1, 2, 3])


class SyncIterator:  # noqa
    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration


class AsyncIterable:  # noqa
    async def __aiter__(self):
        for i in range(3):
            yield i


class AsyncIterator:  # noqa
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.timeout(2)
async def test_is_async_callable():
    """Test the function: `is_async_callable`."""
    assert is_async_callable(async_func)
    assert not is_async_callable(sync_func)
    assert is_async_callable(AsyncCallable())
    assert not is_async_callable(SyncCallable())
    assert not is_async_callable(lambda x: x)
    assert is_async_callable(asyncio.sleep)
    assert not is_async_callable(asyncio.create_task(asyncio.sleep(0)))


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.timeout(2)
async def test_is_callable():
    """Test the function: `is_callable`."""
    assert is_callable(async_func)
    assert is_callable(sync_func)
    assert is_callable(AsyncCallable())
    assert is_callable(SyncCallable())
    assert is_callable(lambda x: x)
    assert is_callable(asyncio.sleep)
    assert not is_callable(asyncio.create_task(asyncio.sleep(0)))


# === iter tests ===


def test_sync_iter():
    """Test the function: `is_sync_iter`."""
    assert is_sync_iter([1, 2, 3])  # list
    assert is_sync_iter((1, 2, 3))  # tuple
    assert is_sync_iter({1, 2, 3})  # set
    assert is_sync_iter({"a": 1, "b": 2})  # dict
    assert is_sync_iter("string")  # str
    assert is_sync_iter(range(5))  # range

    # Test generators
    assert is_sync_iter(sync_gen())
    assert is_sync_iter(sync_gen_expr())

    # Test iterators
    assert is_sync_iter(iter([1, 2, 3]))  # iterator
    assert is_sync_iter(SyncIterable())
    assert is_sync_iter(SyncIterator())

    # Test non-iterables
    assert not is_sync_iter(42)  # int
    assert not is_sync_iter(3.14)  # float
    assert not is_sync_iter(None)  # None
    assert not is_sync_iter(lambda x: x)  # function
    with open(__file__) as f:
        assert is_sync_iter(f)

    # Test async iterables
    assert not is_sync_iter(AsyncIterable())
    assert not is_sync_iter(AsyncIterator())
    assert not is_sync_iter(async_gen())
    assert not is_sync_iter(async_gen_expr())


def test_async_iter():
    """Test the function: `is_async_iter`."""
    # Test generators
    assert is_async_iter(async_gen())
    assert is_async_iter(async_gen_expr())
    assert is_async_iter(coroutine_gen())

    # Test iterators
    assert is_async_iter(AsyncIterable())
    assert is_async_iter(AsyncIterator())

    # Test non-iterables
    assert not is_async_iter(42)  # int
    assert not is_async_iter(3.14)  # float
    assert not is_async_iter(None)  # None
    assert not is_async_iter(lambda x: x)  # function
    with open(__file__) as f:
        assert not is_async_iter(f)

    # Test sync iterables
    assert not is_async_iter([1, 2, 3])  # list
    assert not is_async_iter((1, 2, 3))  # tuple
    assert not is_async_iter({1, 2, 3})  # set
    assert not is_async_iter({"a": 1, "b": 2})  # dict
    assert not is_async_iter("string")  # str
    assert not is_async_iter(range(5))  # range
    assert not is_async_iter(iter([1, 2, 3]))  # iterator

    assert not is_async_iter(sync_gen())
    assert not is_async_iter(sync_gen_expr())
    assert not is_async_iter(SyncIterable())
    assert not is_async_iter(SyncIterator())
