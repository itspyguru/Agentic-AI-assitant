from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pathlib import Path
from typing import List

mcp = FastMCP("FileSystem Server")

def get_full_path(path: str) -> str:
    return Path(path).expanduser().resolve()

@mcp.tool
def list_files(path: str) -> List[str]:
    """
    Returns the list of all the files in a given directory

    Arg:
        path (str): Path of the folder to scan

    Return:
        Returns a list of filenames in the given folder
    """

    target = get_full_path(path)
    if not target.exists():
        raise ToolError(f"Path does not exist: {target}")
    if not target.is_dir():
        raise ToolError(f"Not a directory: {target}")

    return [file.name for file in target.iterdir()]


@mcp.tool
def read_file(path: str) -> str:
    """
    Read the content of the given file

    Arg:
        path (str): take the path of the file to be read

    Return:
        returns the content of the file after reading it.
    """

    target = get_full_path(path)
    if not target.exists():
        raise ToolError(f"Path does not exist: {target}")
    if not target.is_file():
        raise ToolError(f"Not a file: {target}")

    return target.read_text()

@mcp.tool
def write_file(path: str, content: str) -> bool:
    """
    Write the given content to a file and saves it.

    Arg:
        path (str): the path of the file
        content (str): the content to be written in the file

    Return:
        Returns True if file is saved with the new content else False
    """

    target = get_full_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return True

@mcp.tool
def search_file_tool(path: str, name: str) -> List[str]:
    """
    Recursively searches for files matching the given name (or glob pattern) under the given directory.

    Arg:
        path (str): the directory to search in
        name (str): exact file name or a glob pattern (e.g. "*.py", "test_*.txt")

    Return:
        List of absolute paths of all matching files. Empty list if nothing matched.
    """

    target = get_full_path(path)
    if not target.exists():
        raise ToolError(f"Path does not exist: {target}")
    if not target.is_dir():
        raise ToolError(f"Not a directory: {target}")

    return [str(match) for match in target.rglob(name)]


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
