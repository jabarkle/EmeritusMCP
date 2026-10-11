"""Independent chatbot: reuses server.py, not agent.py. One question per run."""

import asyncio
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters
from ollama import AsyncClient


async def main():
    question = input("Ask a course question: ")
    llm = AsyncClient(host="http://127.0.0.1:11434", timeout=120)
    messages = [
        {"role": "system", "content": (
            "You are a helpful teaching assistant. Use tools to verify course "
            "details. Never invent deadlines. Explain tool errors honestly."
        )},
        {"role": "user", "content": question},
    ]

    # 1. Connect to the existing server. Use an absolute path if it lives elsewhere.
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).with_name("server.py"))],
    )
    async with Client(server) as mcp:
        # 2. Discover its tools and give their definitions to Ollama.
        discovered = await mcp.list_tools()
        tools = [{"type": "function", "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        }} for tool in discovered.tools]
        allowed = {tool.name for tool in discovered.tools}

        for _ in range(4):
            response = await llm.chat(
                model="llama3.2:3b", messages=messages, tools=tools,
                options={"temperature": 0, "num_predict": 512},
            )
            messages.append(response.message.model_dump(exclude_none=True))
            if not response.message.tool_calls:
                print(response.message.content)
                return

            # 3. Execute requested tools through MCP and return results to the model.
            for call in response.message.tool_calls:
                name, arguments = call.function.name, call.function.arguments
                print(f"Tool requested: {name}({arguments})")
                if name in allowed:
                    result = await mcp.call_tool(name, arguments)
                    content = "\n".join(
                        item.text for item in result.content if item.type == "text"
                    )
                else:
                    content = "Error: that tool is not available."
                messages.append({
                    "role": "tool", "tool_name": name, "content": content,
                })
        print("Stopped after four model turns. Try a simpler question.")


if __name__ == "__main__":
    asyncio.run(main())
