"""Agent runtime wiring for the God Mode build agent."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

# --------------------------------------------------------------------------- #
# LLM plumbing
# --------------------------------------------------------------------------- #

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        _client = OpenAI(api_key=api_key)
    return _client


def llm_call(system_prompt: str, messages: List[Dict[str, str]]) -> str:
    """
    Centralised LLM call so we can easily swap models or log usage later.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.2,
    )
    return response.choices[0].message.content


# --------------------------------------------------------------------------- #
# Tool registry
# --------------------------------------------------------------------------- #

ToolFn = Callable[[Dict[str, Any]], Dict[str, Any]]
TOOLS: Dict[str, ToolFn] = {}


def tool(name: str) -> Callable[[ToolFn], ToolFn]:
    def decorator(func: ToolFn) -> ToolFn:
        TOOLS[name] = func
        return func

    return decorator


# --------------------------------------------------------------------------- #
# Paths + helpers
# --------------------------------------------------------------------------- #

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
ROOT = os.fspath(_DEFAULT_ROOT)
DESIGN_DOCS_DIR = os.path.join(ROOT, "design_docs")
LOG_DIR = os.path.join(ROOT, "logs", "agent_runs")
MEMORY_DIR = os.path.join(ROOT, "memory")
MEMORY_NOTES_PATH = os.path.join(MEMORY_DIR, "notes.jsonl")


def _resolve_repo_root(candidate: Optional[str]) -> Path:
    if candidate:
        return Path(candidate).resolve()
    env_root = os.getenv("GODMODE_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return _DEFAULT_ROOT


def _safe_path(rel_path: str) -> Path:
    candidate = Path(rel_path)
    if not candidate.is_absolute():
        candidate = Path(ROOT) / candidate
    candidate = candidate.resolve()
    root_path = Path(ROOT)
    if not str(candidate).startswith(str(root_path)):
        raise ValueError("path outside project root")
    return candidate


def _set_project_root(repo_root: Optional[str]) -> str:
    global ROOT, DESIGN_DOCS_DIR, LOG_DIR, MEMORY_DIR, MEMORY_NOTES_PATH
    root = _resolve_repo_root(repo_root)
    if not root.is_dir():
        raise ValueError(f"Invalid repo_root: {root}")
    ROOT = os.fspath(root)
    DESIGN_DOCS_DIR = os.path.join(ROOT, "design_docs")
    LOG_DIR = os.path.join(ROOT, "logs", "agent_runs")
    MEMORY_DIR = os.path.join(ROOT, "memory")
    MEMORY_NOTES_PATH = os.path.join(MEMORY_DIR, "notes.jsonl")
    MEMORY_STORE.configure(root)
    return ROOT


# --------------------------------------------------------------------------- #
# Memory utilities
# --------------------------------------------------------------------------- #


class MemoryStore:
    def __init__(self, repo_root: Path):
        self._lock = threading.RLock()
        self.configure(repo_root)

    def configure(self, repo_root: Path) -> None:
        with self._lock:
            root = Path(repo_root)
            self.dir = root / "memory"
            self.path = self.dir / "notes.jsonl"
            self._cache: List[Dict[str, Any]] = []
            self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        notes: List[Dict[str, Any]] = []
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        notes.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        self._cache = notes
        self._loaded = True

    def append(self, text: str, tags: List[str]) -> Dict[str, Any]:
        note = {
            "text": text,
            "tags": tags,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        with self._lock:
            self.dir.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(note) + "\n")
            if self._loaded:
                self._cache.append(note)
        return note

    def _matching_notes(
        self, query: Optional[str], tags: Optional[List[str]], limit: int
    ) -> List[Dict[str, Any]]:
        with self._lock:
            self._ensure_loaded()
            query_l = query.lower() if query else None
            tag_set = set(tags or [])
            results: List[Dict[str, Any]] = []
            for note in reversed(self._cache):
                note_tags = set(note.get("tags") or [])
                if tag_set and not tag_set.issubset(note_tags):
                    continue
                text = str(note.get("text", ""))
                if query_l and query_l not in text.lower():
                    continue
                results.append(note)
                if len(results) >= limit:
                    break
            return results

    def search(self, query: str, tags: Optional[List[str]], limit: int) -> List[Dict[str, Any]]:
        return self._matching_notes(query, tags, limit)

    def latest(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._matching_notes(query=None, tags=None, limit=limit)


MEMORY_STORE = MemoryStore(_DEFAULT_ROOT)
_set_project_root(os.fspath(_DEFAULT_ROOT))


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #


@tool("list_dir")
def list_dir(params: Dict[str, Any]) -> Dict[str, Any]:
    rel = params.get("path", ".")
    try:
        path = _safe_path(rel)
        entries = sorted(os.listdir(path))
        return {"entries": entries}
    except Exception as exc:
        return {"error": str(exc)}


@tool("read_file")
def read_file(params: Dict[str, Any]) -> Dict[str, Any]:
    rel = params.get("path", "")
    try:
        path = _safe_path(rel)
    except Exception as exc:
        return {"error": str(exc)}
    if not path.is_file():
        return {"error": "file does not exist"}
    try:
        return {"content": path.read_text(encoding="utf-8")}
    except Exception as exc:
        return {"error": str(exc)}


@tool("write_file")
def write_file(params: Dict[str, Any]) -> Dict[str, Any]:
    rel = params.get("path", "")
    content = params.get("content", "")
    try:
        path = _safe_path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": os.fspath(path)}
    except Exception as exc:
        return {"error": str(exc)}


@tool("append_file")
def append_file(params: Dict[str, Any]) -> Dict[str, Any]:
    rel = params.get("path", "")
    content = params.get("content", "")
    try:
        path = _safe_path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(content)
        return {"ok": True, "path": os.fspath(path)}
    except Exception as exc:
        return {"error": str(exc)}


SAFE_COMMAND_PREFIXES = [
    "ls",
    "cat ",
    "echo ",
    "pytest",
    "python ",
    "black ",
    "ruff ",
    "docker compose ",
    "git status",
]


@tool("run_shell")
def run_shell(params: Dict[str, Any]) -> Dict[str, Any]:
    cmd = params.get("cmd", "").strip()
    if not cmd:
        return {"error": "missing cmd"}
    if not any(cmd.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES):
        return {"error": f"command not allowed: {cmd}"}
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }
    except Exception as exc:
        return {"error": str(exc)}


@tool("git_status")
def git_status(_: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            "git status --short",
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return {"status": result.stdout}
    except Exception as exc:
        return {"error": str(exc)}


@tool("git_commit")
def git_commit(params: Dict[str, Any]) -> Dict[str, Any]:
    msg = params.get("message", "auto-commit")
    try:
        subprocess.run("git add .", shell=True, cwd=ROOT, check=False)
        result = subprocess.run(
            f'git commit -m "{msg}"',
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
    except Exception as exc:
        return {"error": str(exc)}


@tool("search_design_docs")
def search_design_docs(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query", "")
    if not query:
        return {"error": "missing query"}
    hits = []
    docs_root = Path(DESIGN_DOCS_DIR)
    if not docs_root.is_dir():
        return {"hits": hits}
    query_l = query.lower()
    for path in docs_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if query_l in text.lower():
            hits.append({"file": os.fspath(path.relative_to(Path(ROOT)))})
    return {"hits": hits}


REPO_SEARCH_IGNORE = {"data", "logs", "memory", ".git", "__pycache__", "node_modules"}


@tool("search_repo")
def search_repo(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query", "").strip()
    if len(query) < 3:
        return {"error": "query must be at least 3 characters"}
    limit = int(params.get("limit", 25))
    within = params.get("path")
    try:
        base_path = _safe_path(within) if within else Path(ROOT)
    except Exception as exc:
        return {"error": str(exc)}
    root_root = Path(ROOT)
    if not str(base_path).startswith(str(root_root)):
        base_path = root_root
    matches: List[Dict[str, Any]] = []
    query_l = query.lower()

    for current_root, dirs, files in os.walk(base_path):
        rel_parts = set(Path(current_root).relative_to(root_root).parts)
        dirs[:] = [d for d in dirs if d not in REPO_SEARCH_IGNORE]
        if rel_parts & REPO_SEARCH_IGNORE:
            continue
        for name in files:
            if len(matches) >= limit:
                break
            path = Path(current_root) / name
            rel_parts = set(path.relative_to(root_root).parts)
            if rel_parts & REPO_SEARCH_IGNORE:
                continue
            try:
                if path.stat().st_size > 250_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if query_l in text.lower():
                matches.append({"file": os.fspath(path.relative_to(root_root))})
    return {"results": matches}


# --------------------------------------------------------------------------- #
# Memory tools
# --------------------------------------------------------------------------- #


@tool("store_note")
def store_note(params: Dict[str, Any]) -> Dict[str, Any]:
    text = params.get("text") or params.get("note") or ""
    if not text and isinstance(params, dict) and "content" in params:
        text = params["content"]
    if not text and isinstance(params, dict) and len(params) == 1:
        text = next(iter(params.values()))
    tags = params.get("tags") or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if not text:
        return {"error": "missing text"}
    if not isinstance(tags, list):
        return {"error": "tags must be a list"}
    note = MEMORY_STORE.append(text=text, tags=tags)
    return {"ok": True, "note": note}


@tool("search_notes")
def search_notes(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query", "")
    limit = int(params.get("limit", 5))
    tags = params.get("tags")
    notes = MEMORY_STORE.search(query=query, tags=tags, limit=limit)
    return {"notes": notes}


@tool("recall_notes")
def recall_notes(params: Dict[str, Any]) -> Dict[str, Any]:
    limit = int(params.get("limit", 5))
    notes = MEMORY_STORE.latest(limit=limit)
    return {"notes": notes}


# --------------------------------------------------------------------------- #
# Agent runtime + logging
# --------------------------------------------------------------------------- #


@dataclass
class AgentStep:
    thought: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None


@dataclass
class AgentState:
    goal: str
    history: List[AgentStep] = field(default_factory=list)
    max_steps: int = 40


AGENT_RULES = (
    "You are the God Mode build agent. Study the repository and the design docs "
    "in 'design_docs/' to make concrete progress. Follow these guardrails:\n"
    "1. Inspect existing files and docs before declaring something missing.\n"
    "2. Break large goals into smaller steps and explain your plan when non-trivial.\n"
    "3. After modifying files, re-open them to verify the changes.\n"
    "4. Capture durable insights with store_note so future runs have full recall.\n"
    "5. Prefer precise tool calls over speculation; if blocked, explain the blocker."
)


class GodModeAgent:
    def __init__(self, goal: str, repo_root: Optional[str] = None):
        active_root = _set_project_root(repo_root)
        self.state = AgentState(goal=goal)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
        self.log_path = Path(LOG_DIR) / f"agent_run_{timestamp}.log"
        self._log(f"=== NEW RUN {timestamp} ===")
        self._log(f"ROOT: {active_root}")
        self._log(f"GOAL: {goal}")

    def _log(self, text: str) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except Exception:
            pass

    def run(self) -> str:
        for step_index in range(self.state.max_steps):
            messages = self._build_messages()
            reply = llm_call(self._system_prompt(), messages)
            self._log(f"\n--- STEP {step_index + 1} RAW REPLY ---")
            self._log(reply)

            try:
                action = json.loads(reply)
            except json.JSONDecodeError:
                step = AgentStep(thought=reply)
                self.state.history.append(step)
                self._log("[PARSE ERROR] treated reply as pure thought")
                continue

            if not isinstance(action, dict):
                step = AgentStep(thought=str(action))
                self.state.history.append(step)
                self._log("[STRUCTURE ERROR] reply was not a JSON object")
                continue

            thought = action.get("thought", "")
            tool_name = action.get("tool")
            tool_input = action.get("tool_input", {})
            if not isinstance(tool_input, dict):
                if isinstance(tool_input, str):
                    tool_input = {"path": tool_input}
                else:
                    self._log("[STRUCTURE ERROR] tool_input was not an object; coercing to empty dict")
                    tool_input = {}
            step = AgentStep(thought=thought, tool_name=tool_name, tool_input=tool_input)

            self._log(f"THOUGHT: {thought}")
            self._log(f"TOOL: {tool_name}")
            self._log(f"TOOL_INPUT: {tool_input}")

            if tool_name is None:
                self.state.history.append(step)
                self._log("AGENT SIGNALLED COMPLETION.")
                self._log(f"FINAL THOUGHT: {thought}")
                return thought

            tool_fn = TOOLS.get(tool_name)
            if not tool_fn:
                result = {"error": f"unknown tool: {tool_name}"}
            else:
                result = tool_fn(tool_input)
            step.tool_result = result
            self._log(f"TOOL_RESULT: {result}")
            self.state.history.append(step)

        self._log("MAX STEPS REACHED WITHOUT COMPLETION.")
        return "Reached max steps without finishing."

    def _system_prompt(self) -> str:
        available_tools = ", ".join(sorted(TOOLS.keys()))
        return (
            f"{AGENT_RULES}\n"
            f"Available tools: {available_tools}.\n"
            "Always respond in strict JSON with keys: thought, tool, tool_input. "
            "Set tool to null when you believe the goal is fully satisfied."
        )

    def _build_messages(self) -> List[Dict[str, str]]:
        history_snippets = []
        for step in self.state.history[-6:]:
            history_snippets.append(
                f"Thought: {step.thought}\n"
                f"Tool: {step.tool_name}\n"
                f"Tool input: {step.tool_input}\n"
                f"Tool result: {step.tool_result}\n"
                "-----"
            )
        memory_snippets = MEMORY_STORE.latest(limit=3)
        if memory_snippets:
            formatted = []
            for note in memory_snippets:
                timestamp = note.get("timestamp", "unknown")
                text = note.get("text")
                if not text:
                    text = note.get("message") or note.get("message_content")
                if not text:
                    text = json.dumps({k: v for k, v in note.items() if k != "timestamp"})
                formatted.append(f"- {timestamp}: {text}")
            memory_text = "\n".join(formatted)
        else:
            memory_text = "(no notes stored yet)"
        content = (
            f"GOAL: {self.state.goal}\n\n"
            f"Persistent memory (latest):\n{memory_text}\n\n"
            "Recent steps:\n"
            f"{chr(10).join(history_snippets) if history_snippets else '(none yet)'}"
        )
        return [{"role": "user", "content": content}]
