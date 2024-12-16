"""Test the `File` resource."""

from demistar.resource.file import File
import pytest
import pathlib
import tempfile
import io
import asyncio


def test_file_resource_read_sync():
    """Test the file resource with sync read."""
    with tempfile.TemporaryDirectory() as temp_dir:
        content = "line 1\nline 2\nline 3\n"
        path = pathlib.Path(temp_dir) / "test_file_resource.txt"
        with open(path.as_posix(), "w") as f:
            f.write(content)

        with File(path) as file:
            buffer = io.StringIO()
            for line in file:
                buffer.write(line)
            assert buffer.getvalue() == content


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.timeout(1)
async def test_file_resource_read_async():
    """Test the file resource with async read."""
    with tempfile.TemporaryDirectory() as temp_dir:
        content = "line 1\nline 2\nline 3\n"
        path = pathlib.Path(temp_dir) / "test_file_resource.txt"
        with open(path.as_posix(), "w") as f:
            f.write(content)

        async with File(path) as file:
            buffer = io.StringIO()
            async for line in file:
                buffer.write(line)
            assert buffer.getvalue() == content


def test_file_resource_write_sync():
    """Test the file resource with sync write."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = pathlib.Path(temp_dir) / "test_file_resource.txt"
        with File(path, "w") as file:
            file.__consume__(["line 1\n", "line 2\n", "line 3\n"])
        assert path.read_text() == "line 1\nline 2\nline 3\n"

    # try also with consume


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.timeout(1)
async def test_file_resource_write_async():
    """Test the file resource with async write."""

    async def async_lines():
        for line in ["line 1\n", "line 2\n", "line 3\n"]:
            await asyncio.sleep(0)
            yield line

    with tempfile.TemporaryDirectory() as temp_dir:
        path = pathlib.Path(temp_dir) / "test_file_resource.txt"
        async with File(path, "w") as file:
            await file.__aconsume__(async_lines())
        assert path.read_text() == "line 1\nline 2\nline 3\n"
