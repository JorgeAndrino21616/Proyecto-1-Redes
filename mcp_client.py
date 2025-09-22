import json
import os
import subprocess
import threading
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "mcp.log"

_counter_lock = threading.Lock()
_request_counter = 0

def _next_id():
    global _request_counter
    with _counter_lock:
        _request_counter += 1
        return _request_counter

def _log(line: str):
    ts = datetime.utcnow().isoformat() + "Z"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def start_mcp(command_args):
    """
    Launch an MCP server over stdio.
    command_args: list of tokens for subprocess,
    Returns a Popen with pipes.
    """
    proc = subprocess.Popen(
        command_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    _log(f"START {' '.join(command_args)} (pid={proc.pid})")
    return proc

def call_mcp(proc, method: str, params: dict | None = None, timeout: float = 30.0):
    """
    Send a single JSON-RPC request and wait for a single-line JSON response.
    """
    if proc.poll() is not None:
        raise RuntimeError("MCP process is not running.")
    req = {
        "jsonrpc": "2.0",
        "id": _next_id(),
        "method": method,
        "params": params or {}
    }
    line = json.dumps(req, ensure_ascii=False)
    _log(f">>> {line}")
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

    resp_line = proc.stdout.readline()
    if not resp_line:
        err = proc.stderr.read() if proc.stderr else ""
        raise RuntimeError(f"No response from MCP server. Stderr:\n{err}")
    resp_line = resp_line.strip()
    _log(f"<<< {resp_line}")
    data = json.loads(resp_line)
    if "error" in data:
        msg = data["error"].get("message", "Unknown MCP error")
        raise RuntimeError(msg)
    return data.get("result")
