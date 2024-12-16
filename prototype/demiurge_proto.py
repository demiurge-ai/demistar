"""Prototyping."""
# from demistar import Component, Sensor, Actuator, From, To, Resource

# from fastapi.responses import JSONResponse, StreamingResponse
# from fastapi import Request
# import io


# class Route:  # fastapi support!
#     def __init__(self, path: str):
#         self.path = path


# # placeholder types that will be implemented later
# class Screenshot:
#     pass


# class DesktopSensor:  # the sensor that senses the desktop
#     pass


# class DesktopActuator:  # The actuator that is used to interact with the desktop
#     pass


# class LVLM:  # the large vision/language model as a resource!
#     pass


# class DemiurgeAgent:
#     """The demiurage agent needs to do lots of things, we need to streamline this.

#     The demiurage agent needs to:
#     - handle FastAPI routes from the frontend
#         - prompts, abort + other requests
#     - make and handle vector database queries
#     - query ML models/APIs
#     - Sense the screen
#     - Take actions via peripheral devices (click, keyboard, move mouse, etc).
#     """

#     def extract_ui_layout(
#         self,
#         observation: Screenshot = From(DesktopSensor),
#         action: Screenshot = To(LayoutExtractor),
#     ) -> str:
#         # this could even be done inside the DesktopSensor,
#         # we can test/deploy alternative models for this!
#         pass

#     def extract(self, observation: From(extract_ui_layout)) -> str:
#         pass

#     def read_file(self, file: From(File("..."))) -> str:
#         pass

#     @property
#     def ui_layout(self) -> str:
#         pass

#     @ui_layout.setter
#     def ui_layout(self, ui_layout: str = From(extract_ui_layout)):
#         # this will automatically be called with the result of `extract_ui_layout`! - how cool.
#         pass  # its just a demo, we could easily set the value in `extract_ui_layout` directly.

#     # ====== handle frontendUI requests! ====== #

#     async def handle_prompt(
#         self,
#         prompt: Request = From(Route("/prompt")),  # request from frontend
#         ui_layout: str = From(ui_layout),  # latest UI layout
#         query: str = To(LVLM),  # LVLM is a resource (an ML model)
#     ):
#         # send the query to the LVLM, this will start a response stream in `handle_lvlm_response`,
#         # which will complete the FastAPI Request.
#         pass

#     async def frontend_response(
#         self,
#         text_stream: str = From(LVLM),
#         response_stream: StreamingResponse = To(Route("/prompt")),
#     ):
#         async for text_chunk in text_stream:
#             yield text_chunk  # do some processing here perhaps?

#     async def assist_response(
#         self,
#         text_stream: str = From(LVLM),
#         response_stream: str = To(DesktopActuator),
#     ):
#         # from the LVLM response, we need to extract the actions to take, or construct a plan and execute it.
#         # this plan can be executed as a sequence of actions yielded to the DesktopActuator.
#         # first gather the response
#         response_buffer = io.StringIO()
#         async for text_chunk in text_stream:
#             response_buffer.write(text_chunk)

#         # build a plan
#         async for action in self.plan(response_buffer):
#             yield action  # these may include timings etc.

#     def handle_abort(
#         self,
#         abort: str = From(Route("/abort")),
#         response: JSONResponse = To(Route(...)),
#     ):
#         pass  # here we could set a flag to abort the current plan/LVLM response
