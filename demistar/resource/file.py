"""Resource that can be used to read/write text files."""

from .resource import Resource

import aiofiles
import pathlib


class File(Resource[str, str]):
    """A file resource that iterates over lines from a file."""

    def __init__(self, path: str | pathlib.Path, mode: str = "r", **kwargs):
        """Construct a file resource.

        Args:
            path: The path to the file.
            mode: The mode to open the file in.
            **kwargs: Additional named arguments.
        """
        super().__init__(**kwargs)
        self.path = pathlib.Path(path)
        self._mode = mode
        self._file = None

    # ==== sync ==== #

    def put_nowait(self, item: str) -> None:
        """Write a line to the file synchronously."""
        self._file.write(item)

    def get_nowait(self) -> str:
        """Get next line synchronously."""
        line = self._file.readline()
        if not line:
            raise StopIteration
        return line

    def __enter__(self):
        assert self._file is None
        self._file = open(self.path.as_posix(), mode=self._mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
        self._file = None

    # ==== async ==== #

    async def put(self, item: str) -> None:
        """Write a line to the file."""
        await self._file.write(item)

    async def get(self) -> str:
        """Get next line asynchronously."""
        line = await self._file.readline()
        if not line:  # EOF
            raise StopAsyncIteration
        return line

    async def __aenter__(self):
        assert self._file is None
        self._file = await aiofiles.open(self.path.as_posix(), mode=self._mode)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._file.close()
        self._file = None
