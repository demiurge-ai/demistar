"""TODO."""

from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Any
from demistar.extras.fastapi import FastAPIAgent, Route, From, sense, attempt


class LogEntry:
    def __init__(self, observation: dict[str, Any]):
        self.observation = observation


class Agent(FastAPIAgent):
    def __init__(self):
        super().__init__()

    async def foo(self) -> str:
        return "foo"

    @sense(route="/message")
    async def prompt(self, request: Request, foo=From(foo)) -> dict[str, Any]:
        return {"prompt": "Hello"}
        # return request.json()

    @attempt(route="/message")
    async def answer(self, observation=From(prompt)) -> JSONResponse:
        return JSONResponse(
            content={"prompt": f"This was your prompt: `{observation['prompt']}`"}
        )

    @attempt()
    async def log(self, observation=From(prompt)) -> LogEntry:
        return LogEntry(observation)

    async def _run(self, request: Request) -> str:
        pass


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = Agent()
        for route in Route.build_routes(agent):
            await route(None)

    asyncio.run(main())
