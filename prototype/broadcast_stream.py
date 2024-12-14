import asyncio
from typing import AsyncGenerator, Set, TypeVar, AsyncIterator
import weakref

T = TypeVar("T")


class SharedAsyncGenerator:
    def __init__(self, source: AsyncGenerator[T, None]):
        self.source = source
        self.subscribers: set[asyncio.Queue] = weakref.WeakSet()

    async def subscribe(self) -> AsyncIterator[T]:
        queue = asyncio.Queue()
        self.subscribers.add(queue)

        try:
            while True:
                item = await queue.get()
                if item is StopAsyncIteration:  # Special signal to stop
                    break
                yield item
        finally:
            print("Unsubscribing...")
            self.subscribers.discard(queue)

    def unsubscribe(self, queue: asyncio.Queue):
        self.subscribers.discard(queue)
        queue.put_nowait(StopAsyncIteration)

    async def broadcast(self):
        try:
            async for item in self.source:
                for queue in self.subscribers:
                    await queue.put(item)
        finally:
            pass


# Example usage with different ways to exit:
async def demo():
    async def number_generator() -> AsyncGenerator[int, None]:
        for i in range(100):
            await asyncio.sleep(0.1)
            yield i

    broadcaster = SharedAsyncGenerator(number_generator())

    # Method 1: Using break
    async def subscriber(name: str):
        print(f"{name} subscribing...")
        async for item in broadcaster.subscribe():
            print(f"{name} received: {item}")
            if item >= 5:  # Exit condition
                print(f"{name} exiting after receiving 5")
                break

    # Start subscribers
    await asyncio.gather(broadcaster.broadcast(), subscriber("sub-1"))


if __name__ == "__main__":
    asyncio.run(demo())
