from demistar import Component, Sensor, Actuator, From, To, Resource

from fastapi.responses import JSONResponse
from fastapi import Request


def route(path: str):
    def _route(fun):
        return fun

    return _route


class DB:
    pass


class Agent:
    def db_query(self, observation: str = From(Sensor), action: str = To(DB)) -> str:
        # query every time a new observation arrives in Sensor
        # set the action to the desired query
        pass

    def handle_db_query(
        self,
        query: str = From(db_query),
        result: str = From(DB),
    ):
        # this will be called with the result of the db query that was performed in `db_query`.
        # query will contain the query that was performed, and result will contain the result of the query.
        pass

    def from_device(self, observation: str = From(Sensor)):
        # example that will gather observations from a sensor, we can process
        # and store the observations here.
        pass

    def to_device(self, action: str = To(Actuator)) -> str:
        # example that will send the action to the actuator
        pass

    @route("/message")  # familiar fastapi route definition
    def route(self, observation: Request = From(...), action: JSONResponse = To(...)):
        pass
