from .resource import Resource

import aiofiles
import pathlib


class File(Resource[str]):
    """A file resource that iterates over lines from a file."""

    def __init__(self, path: str | pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        self.path = pathlib.Path(path)
        self._file = None

    def get_nowait(self) -> str:
        """Get next line synchronously."""
        return self._file.readline()

    def __enter__(self):
        assert self._file is None
        self._file = open(self.path.as_posix())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
        self._file = None

    async def get(self) -> str:
        """Get next line asynchronously."""
        line = await self._file.readline()
        if not line:  # EOF
            raise StopAsyncIteration

        return line.rstrip("\n")

    async def __aenter__(self):
        assert self._file is None
        self._file = await aiofiles.open(self.path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._file.close()
        self._file = None
