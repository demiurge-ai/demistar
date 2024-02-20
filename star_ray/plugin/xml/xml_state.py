from typing import Dict
from lxml import etree as ET
from .query_xpath import QueryXPath
from ...event import ErrorResponse, SelectResponse, UpdateResponse


class XMLState:
    """
    A class to represent and manipulate XML state data.

    This class provides a structured way to interact with XML data using XPath queries (see `XPathQuery`) for selection and updates. It supports namespace definitions to handle XML data that includes namespaces.

    Methods:
        __select__(query: QueryXPath) -> ResponseSelect | ResponseError: Executes a read-only XPath query on the XML data and returns a `ResponseSelect` object for successful queries or a `ResponseError` object in case of an error.
        __update__(query: QueryXPath) -> ResponseUpdate | ResponseError: Executes a write XPath query on the XML data and returns a `ResponseUpdate` object for successful updates or a `ResponseError` object in case of an error.

    The `__select__` method is designed to be safe for parallel execution, allowing for efficient read operations on the XML data.
    The `__update__` method handles write operations and modifies the XML state.
    """

    def __init__(self, xml: str, namespaces: Dict[str, str] = None):
        super().__init__()
        self._root = ET.fromstring(xml)  # pylint: disable=I1101
        self._namespaces = dict() if namespaces is None else namespaces

    def __select__(self, query: QueryXPath) -> SelectResponse | ErrorResponse:
        # TODO this is a read only query and can be executed in parallel
        return query.__select__("environment", self._root, namespaces=self._namespaces)

    def __update__(self, query: QueryXPath) -> UpdateResponse | ErrorResponse:
        # TODO this is a write query
        return query.__update__("environment", self._root, namespaces=self._namespaces)
