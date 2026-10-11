"""A small desktop GUI. Run: python app.py"""

import asyncio
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from agent import DEFAULT_MODEL, ask


def main():
    root = tk.Tk()
    root.title("MCP in action | Course assistant")
    root.geometry("1050x780")
    root.minsize(800, 620)
    root.configure(padx=20, pady=16)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(5, weight=1)
    root.rowconfigure(7, weight=2)

    ttk.Label(root, text="One question. Two levels of access.",
              font=("Segoe UI", 20, "bold")).grid(sticky="w")
    ttk.Label(root, text="Same local model and prompt. MCP gives it a tool to read the live course schedule.").grid(
        row=1, sticky="w", pady=(4, 16))

    settings = ttk.Frame(root)
    settings.grid(row=2, sticky="ew")
    settings.columnconfigure(1, weight=1)
    ttk.Label(settings, text="Question").grid(row=0, column=0, padx=(0, 10))
    question = ttk.Entry(settings, font=("Segoe UI", 12))
    question.insert(0, "When is Assignment 3 due?")
    question.grid(row=0, column=1, sticky="ew", pady=5)
    ttk.Label(settings, text="Ollama model").grid(row=1, column=0, padx=(0, 10))
    model = ttk.Entry(settings)
    model.insert(0, DEFAULT_MODEL)
    model.grid(row=1, column=1, sticky="ew", pady=5)

    controls = ttk.Frame(root)
    controls.grid(row=3, sticky="w", pady=12)
    status = tk.StringVar(value="Start with MCP off, then run the same question with MCP on.")
    ttk.Label(root, textvariable=status).grid(row=4, sticky="w", pady=(0, 8))

    answers = ttk.Frame(root)
    answers.grid(row=5, sticky="nsew")
    answers.columnconfigure((0, 1), weight=1)
    answers.rowconfigure(0, weight=1)

    def output(parent, title, column):
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 8))
        box = ScrolledText(frame, wrap="word", height=7, width=35,
                           font=("Segoe UI", 11), state="disabled")
        box.pack(fill="both", expand=True)
        return box

    boxes = [output(answers, "1. Without MCP", 0), output(answers, "2. With MCP", 1)]
    ttk.Label(root, text="Live trace — tool discovery, model requests, and server results",
              font=("Segoe UI", 11, "bold")).grid(row=6, sticky="w", pady=(14, 6))
    trace = ScrolledText(root, wrap="word", height=13, font=("Consolas", 10), state="disabled")
    trace.grid(row=7, sticky="nsew")
    ttk.Label(root, text="Try it live: edit the Assignment 3 deadline in assignments.json, save, then ask with MCP again.").grid(
        row=8, sticky="w", pady=(12, 0))

    events = Queue()

    def write(box, text, clear=False):
        box.configure(state="normal")
        if clear:
            box.delete("1.0", "end")
        box.insert("end", text)
        box.see("end")
        box.configure(state="disabled")

    def run(use_mcp):
        prompt, selected_model = question.get().strip(), model.get().strip()
        if not prompt or not selected_model:
            status.set("Enter a question and model name first.")
            return
        for button in buttons:
            button.configure(state="disabled")
        write(boxes[int(use_mcp)], "", clear=True)
        write(trace, f"QUESTION: {prompt}\nMODEL: {selected_model}\n\n", clear=True)
        status.set("Running with MCP..." if use_mcp else "Running without MCP...")

        def work():
            try:
                answer = asyncio.run(ask(prompt, use_mcp, selected_model,
                                         log=lambda text: events.put(("trace", text))))
            except Exception as exc:
                answer = f"Could not complete the request: {exc}\n\nCheck that Ollama is running and this model is installed. See README.md for troubleshooting."
                events.put(("trace", repr(exc)))
            events.put(("done", (use_mcp, answer)))

        Thread(target=work, daemon=True).start()

    buttons = [ttk.Button(controls, text="1. Ask without MCP", command=lambda: run(False)),
               ttk.Button(controls, text="2. Ask with MCP", command=lambda: run(True))]
    for i, button in enumerate(buttons):
        button.grid(row=0, column=i, padx=(0, 12))

    def poll():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == "trace":
                    write(trace, value + "\n\n")
                else:
                    use_mcp, answer = value
                    write(boxes[int(use_mcp)], answer, clear=True)
                    status.set("Finished. Each run starts a fresh conversation.")
                    for button in buttons:
                        button.configure(state="normal")
        except Empty:
            pass
        root.after(100, poll)

    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
