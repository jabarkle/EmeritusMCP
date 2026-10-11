# MCP in action: a course assistant

A small teaching demo: ask **"When is Assignment 3 due?"** with and without MCP.
The same local model cannot verify your private course schedule on its own. With
MCP, it discovers a tool, asks the server to read the schedule, and uses the result
to answer. The GUI shows both answers and the actual tool calls.

**Local only. No API key, paid service, database, or agent framework.**

## Setup

Install **Python 3.11+** and [Ollama](https://ollama.com/download). Keep Ollama
running, then download the small model (about 2 GB; needed only once):

```sh
ollama pull llama3.2:3b
```

Open a terminal in this folder after cloning/downloading it.

**Windows / PowerShell** (no environment activation required):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

**macOS / Linux:**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

The desktop window opens directly; there is no browser URL. Tkinter ships with
most desktop Python installations. On Ubuntu/Debian, install `python3-tk` and
`python3-venv` if needed. A desktop session is required for the GUI.

## Five-minute classroom demo

1. Leave the question as **When is Assignment 3 due?** Click **Ask without MCP**.
   The model should say it cannot verify the schedule. It receives no course data.
2. Click **Ask with MCP**. Watch the trace: discovery, the model's tool request,
   the JSON returned by the server, and the answer. The sample deadline is
   **October 30, 2026, at 11:59 PM America/New_York**.
3. Open `assignments.json` in a text editor. Change Assignment 3's `due` value to
   `2026-11-06 at 5:00 PM America/New_York` and **save**. Ask with MCP again.
   The answer should now use November 6. No app restart or retraining is needed.
4. Ask **When is Assignment 99 due?** with MCP. The tool reports that it was not
   found; the agent should explain that rather than invent a deadline.
5. Show `server.py`: the decorator exposes the function; its docstring and type
   hint describe the tool to clients. Then show `agent.py`: discovery, model
   request, MCP execution, and the tool result sent back to the model.

All course data is fictional. Each click starts a fresh conversation. Temperature
is zero for consistency, but tool choice and answer wording are still model behavior.
The app never fabricates a tool call to make the demo pass.

## What students should learn

```text
GUI or CLI -> agent.py (host + MCP client)
                |                  |
                | chat + schemas   | MCP over stdio
                v                  v
              Ollama           server.py -> assignments.json
                |
                +-- requests a tool; the host executes it through MCP
```

**Tools provide access to current information. MCP standardizes discovery and
invocation so the server can be reused by compatible clients.** The model itself
does not open the file or speak MCP; the host bridges its tool requests to MCP.
Here, the client starts the server as a separate local process and communicates
over stdin/stdout. No server port is needed.

A direct Python function or REST integration could also provide this data. This
demo demonstrates failure **without access to the data**, not that MCP is the
only solution. Its benefit is a reusable tool interface instead of a custom
integration for every agent. Our host discovers the tool schema from the server;
it does not import `get_assignment` or read the schedule itself.

## Files

| File | Purpose |
| --- | --- |
| `server.py` | The complete MCP server and its one read-only tool |
| `assignments.json` | The editable source of truth |
| `agent.py` | Ollama + MCP connection and a small bounded agent loop |
| `app.py` | Tkinter GUI with two answer panels and a live trace |
| `requirements.txt` | Exact versions of the two Python dependencies |
| `smoke_test.py` | Tests real MCP discovery, lookup, updates, and errors without a model |

## Run without the GUI

Using the Python executable from your environment:

```sh
python agent.py
python agent.py --mcp
python agent.py --mcp "How do I submit Assignment 2?"
python smoke_test.py
```

On Windows without activation, substitute `.\.venv\Scripts\python.exe` for
`python`; on macOS/Linux substitute `.venv/bin/python`.

To reuse the server in another MCP client, configure its stdio command as the
**absolute path to this environment's Python**, with the **absolute path to
`server.py`** as its argument. The server resolves its JSON file relative to
itself, so the client's working directory does not matter. Running `server.py`
directly will wait for MCP messages; it is not an interactive chat program.

## Troubleshooting

- **Cannot connect to Ollama:** open the Ollama application, or run `ollama serve`
  in another terminal if it is not already running. This demo uses localhost port 11434.
- **Model not found:** run `ollama list`, then pull `llama3.2:3b` or enter an
  installed tool-capable model's name in the GUI. An embedding model cannot chat.
- **No tool call / incorrect answer:** inspect the trace. Try the exact example
  question and the default model. A model can still make mistakes; MCP does not
  guarantee correct reasoning.
- **Slow first answer:** Ollama may need to load the model. Requests have a
  120-second timeout; subsequent requests are usually faster.
- **Import error:** install `requirements.txt` with the same Python used to run
  the app. This demo uses the official MCP SDK **2.2.0** (`MCPServer`, `Client`);
  older tutorials may use v1's `FastMCP` and `ClientSession` names.
- **Malformed JSON:** fix `assignments.json` and save it. Tool errors appear in
  the trace. `python -m json.tool assignments.json` can check the file.

Upload the source files to GitHub; `.gitignore` excludes the local environment,
logs, and Python caches. Students install dependencies themselves.

## References

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Python Tkinter](https://docs.python.org/3/library/tkinter.html)
