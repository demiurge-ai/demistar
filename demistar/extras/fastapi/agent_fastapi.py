"""Defines the baseclass for a fastapi agent. This agent will run in a cycle that is independent from the environment."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from collections import defaultdict
from typing import Callable

import uvicorn
import ray
import inspect


from ...agent import Agent


class FastAPIAgent(Agent):
    def __init__(self, host="0.0.0.0", port=7444):
        super().__init__([], [])
        self._app = FastAPI()
        self._host = host
        self._port = port

    def __cycle__(self):
        pass  # cycle doesnt do anything for a fastapi agent, everything is managed asynchronously

    def run(self):
        # run this agent - it is essentially a web server
        config = uvicorn.Config(
            self._app, host=self._host, port=self._port, log_level="info"
        )
        server = uvicorn.Server(config)
        server.run()
