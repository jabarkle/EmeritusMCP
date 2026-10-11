"""Exercise a real MCP subprocess with a temporary copy of the course data."""

import asyncio
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters


async def main():
    source = Path(__file__).parent
    with TemporaryDirectory() as directory:
        folder = Path(directory)
        for name in ("server.py", "assignments.json"):
            shutil.copy(source / name, folder / name)
        server = StdioServerParameters(
            command=sys.executable, args=[str(folder / "server.py")],
        )
        async with Client(server) as client:
            tools = (await client.list_tools()).tools
            assert [tool.name for tool in tools] == ["get_assignment"]
            assert tools[0].input_schema["required"] == ["name"]

            async def lookup(name):
                result = await client.call_tool("get_assignment", {"name": name})
                assert not result.is_error, result
                return json.loads(next(item.text for item in result.content if item.type == "text"))

            schedule = folder / "assignments.json"
            data = json.loads(schedule.read_text(encoding="utf-8"))
            first = await lookup(" assignment 3 ")
            assert first["due"] == data["Assignment 3"]["due"]

            # The same running server must observe changes, not cache the file.
            data["Assignment 3"]["due"] = "2030-01-02 at 5:00 PM America/New_York"
            schedule.write_text(json.dumps(data), encoding="utf-8")
            assert (await lookup("Assignment 3"))["due"] == data["Assignment 3"]["due"]
            assert (await lookup("Assignment 99"))["error"] == "Assignment not found"

            invalid = await client.call_tool("get_assignment", {})
            assert invalid.is_error
            schedule.write_text("invalid JSON", encoding="utf-8")
            assert "Cannot read the schedule" in (await lookup("Assignment 3"))["error"]
    print("PASS: MCP discovery, lookup, live updates, missing assignment, and tool errors.")


if __name__ == "__main__":
    asyncio.run(main())
