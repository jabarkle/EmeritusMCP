"""A complete local MCP server: one read-only tool, one JSON file."""

import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("Course schedule")
SCHEDULE = Path(__file__).with_name("assignments.json")


@mcp.tool()
def get_assignment(name: str) -> dict:
    """Look up a course assignment's current deadline and submission instructions.

    Use the assignment name, for example 'Assignment 3'.
    """
    # Read on every call: saving a new deadline takes effect immediately.
    try:
        assignments = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"error": "Cannot read the schedule. Check assignments.json is valid JSON."}
    for title, details in assignments.items():
        if title.casefold() == name.strip().casefold():
            return {"name": title, **details}
    return {"error": "Assignment not found", "available": list(assignments)}


if __name__ == "__main__":
    # stdout belongs to the MCP protocol; send any debug prints to stderr.
    mcp.run(transport="stdio")
