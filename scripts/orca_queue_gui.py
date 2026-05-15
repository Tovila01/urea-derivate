#!/usr/bin/env python3
from __future__ import annotations

import re
import os
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk


ROOT = Path(
    sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DFT_PROJECT_ROOT", Path(__file__).resolve().parents[1])
).expanduser().resolve()
JOBS_DIR = ROOT / "jobs"
DONE_MARKER = "ORCA TERMINATED NORMALLY"
REFRESH_MS = 5000
TAIL_LINES = 80


@dataclass(frozen=True)
class Job:
    name: str
    inp: Path
    out: Path
    status: str


def read_text_tail(path: Path, lines: int = TAIL_LINES) -> str:
    if not path.exists():
        return "No output file yet."
    try:
        data = path.read_text(errors="replace").splitlines()
    except OSError as exc:
        return f"Could not read output: {exc}"
    return "\n".join(data[-lines:]) if data else "Output file is empty."


def output_done(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        return DONE_MARKER in path.read_text(errors="ignore")
    except OSError:
        return False


def process_table() -> str:
    try:
        return subprocess.check_output(
            ["ps", "-axo", "pid=,ppid=,command="],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return ""


def running_job_names() -> set[str]:
    table = process_table()
    names: set[str] = set()
    for match in re.finditer(r"([A-Za-z0-9_]+_opt_freq)(?:\.inp|\.gbw|\.scfgrad\.inp|\b)", table):
        names.add(match.group(1))
    return names


def discover_jobs() -> list[Job]:
    running = running_job_names()
    jobs: list[Job] = []
    for inp in sorted(JOBS_DIR.rglob("*_opt_freq.inp")):
        out = inp.with_suffix(".out")
        rel = inp.relative_to(JOBS_DIR).with_suffix("").as_posix()
        base = inp.stem
        if output_done(out):
            status = "done"
        elif base in running:
            status = "running"
        else:
            status = "queued"
        jobs.append(Job(rel, inp, out, status))
    return jobs


class QueueGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ORCA Queue Monitor")
        self.geometry("1180x760")
        self.minsize(980, 620)

        self.jobs: dict[str, Job] = {}
        self.selected_job: Job | None = None
        self.auto_tail = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Scanning...")

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(3, weight=1)

        ttk.Button(toolbar, text="Refresh", command=self.refresh).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(toolbar, text="Show Tail", command=self.show_selected_tail).grid(row=0, column=1, padx=(0, 8))
        ttk.Checkbutton(toolbar, text="Auto tail selected", variable=self.auto_tail).grid(row=0, column=2, padx=(0, 16))
        ttk.Label(toolbar, textvariable=self.status_var).grid(row=0, column=3, sticky="w")

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        lists = ttk.Frame(pane)
        lists.columnconfigure(0, weight=1)
        lists.columnconfigure(1, weight=1)
        lists.columnconfigure(2, weight=1)
        lists.rowconfigure(1, weight=1)
        pane.add(lists, weight=3)

        self.listboxes: dict[str, tk.Listbox] = {}
        for col, status in enumerate(("running", "queued", "done")):
            label = ttk.Label(lists, text=status.title())
            label.grid(row=0, column=col, sticky="w", padx=(0 if col == 0 else 8, 4), pady=(0, 4))

            frame = ttk.Frame(lists)
            frame.grid(row=1, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

            box = tk.Listbox(frame, exportselection=False, activestyle="dotbox")
            scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=box.yview)
            box.configure(yscrollcommand=scroll.set)
            box.grid(row=0, column=0, sticky="nsew")
            scroll.grid(row=0, column=1, sticky="ns")
            box.bind("<<ListboxSelect>>", self.on_select)
            box.bind("<Double-Button-1>", lambda _event: self.show_selected_tail())
            self.listboxes[status] = box

        tail_frame = ttk.Frame(pane)
        tail_frame.columnconfigure(0, weight=1)
        tail_frame.rowconfigure(1, weight=1)
        pane.add(tail_frame, weight=2)

        self.tail_title = tk.StringVar(value="Tail")
        ttk.Label(tail_frame, textvariable=self.tail_title).grid(row=0, column=0, sticky="w", pady=(0, 4))

        text_frame = ttk.Frame(tail_frame)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.tail = tk.Text(text_frame, wrap="none", font=("Menlo", 11))
        tail_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.tail.yview)
        tail_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.tail.xview)
        self.tail.configure(yscrollcommand=tail_y.set, xscrollcommand=tail_x.set)
        self.tail.grid(row=0, column=0, sticky="nsew")
        tail_y.grid(row=0, column=1, sticky="ns")
        tail_x.grid(row=1, column=0, sticky="ew")

    def refresh(self) -> None:
        previous = self.selected_job.name if self.selected_job else None
        jobs = discover_jobs()
        self.jobs = {job.name: job for job in jobs}

        counts = {"done": 0, "running": 0, "queued": 0}
        for status, box in self.listboxes.items():
            box.delete(0, tk.END)
            for job in [j for j in jobs if j.status == status]:
                counts[status] += 1
                box.insert(tk.END, job.name)
                if previous == job.name:
                    box.selection_set(tk.END)
                    box.see(tk.END)
                    self.selected_job = job

        total = len(jobs)
        self.status_var.set(
            f"{counts['running']} running | {counts['queued']} queued | {counts['done']} done | {total} total"
        )

        if self.auto_tail.get() and self.selected_job:
            self.show_tail(self.selected_job)
        elif not self.selected_job:
            running = [job for job in jobs if job.status == "running"]
            if running:
                self.selected_job = running[0]
                self.show_tail(running[0])

        self.after(REFRESH_MS, self.refresh)

    def on_select(self, event: tk.Event) -> None:
        box = event.widget
        if not isinstance(box, tk.Listbox) or not box.curselection():
            return
        name = box.get(box.curselection()[0])
        self.selected_job = self.jobs.get(name)
        if self.selected_job and self.auto_tail.get():
            self.show_tail(self.selected_job)

    def show_selected_tail(self) -> None:
        if self.selected_job:
            self.show_tail(self.selected_job)

    def show_tail(self, job: Job) -> None:
        self.tail_title.set(f"Tail: {job.name} ({job.status})")
        self.tail.delete("1.0", tk.END)
        self.tail.insert(tk.END, read_text_tail(job.out))
        self.tail.see(tk.END)


if __name__ == "__main__":
    QueueGui().mainloop()
