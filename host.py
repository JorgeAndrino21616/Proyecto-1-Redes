import os, sys, json, shlex
from llm_client import ask_llm
from mcp_client import start_mcp, call_mcp, LOG_FILE

BANNER = "=== Host MCP — type /help for commands ==="

class Host:
    def __init__(self):
        self.history = []
        self.mcp_procs = {}

    def do_llm(self, text):
        self.history.append({"role":"user","content":text})
        try:
            reply = ask_llm(self.history)
        except Exception as e:
            reply = f"[LLM error] {e}"
        self.history.append({"role":"assistant","content":reply})
        print(reply)

    def do_use(self, alias, cmdline):
        if alias in self.mcp_procs:
            print(f"[use] '{alias}' is already running.")
            return
        args = shlex.split(cmdline)
        if len(args) == 1 and args[0].endswith(".py"):
            script = args[0]
            if not os.path.isabs(script):
                here = os.path.dirname(__file__)
                script = os.path.join(here, script)
            args = [sys.executable, script]
        proc = start_mcp(args)
        self.mcp_procs[alias] = proc
        print(f"[use] started '{alias}': {args}")

    def do_call(self, alias, method, params_json="{}"):
        if alias not in self.mcp_procs:
            print(f"[call] server '{alias}' not found. Use /use first.")
            return
        try:
            params = json.loads(params_json) if params_json.strip() else {}
        except json.JSONDecodeError as e:
            print(f"[call] invalid JSON in params: {e}")
            return
        try:
            result = call_mcp(self.mcp_procs[alias], method, params)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[call] error: {e}")

    def scenario_git_readme(self, alias_git, repo_path):
        self.do_call(alias_git, "tools/call", json.dumps({"name":"git_init","arguments":{"path": repo_path}}))
        self.do_call(alias_git, "tools/call", json.dumps({"name":"fs_write","arguments":{"path": f"{repo_path}/README.md", "content": "# Hola MCP\\n"}}))
        self.do_call(alias_git, "tools/call", json.dumps({"name":"git_add","arguments":{"path": repo_path, "files": ["README.md"]}}))
        self.do_call(alias_git, "tools/call", json.dumps({"name":"git_commit","arguments":{"path": repo_path, "message": "feat: add README via MCP"}}))
        print("[scenario] Repo created with README and initial commit.")

    def print_history(self):
        for i, msg in enumerate(self.history, 1):
            role = msg["role"]
            content = msg["content"]
            print(f"{i:02d} [{role}] {content}")

    def close(self):
        for a, p in self.mcp_procs.items():
            try:
                p.terminate()
            except:
                pass

def main():
    h = Host()
    print(BANNER)
    here = os.path.dirname(__file__)
    default_lol     = f"{sys.executable} {os.path.join(here, 'mcp-server.py')}"
    default_fs      = "python -m mcp_servers.filesystem"
    default_git     = "python -m mcp_servers.git"
    default_arx   = f"{sys.executable} {os.path.join(here, 'mcp-server-compañero-2.py')}"


    try:
        while True:
            line = input("> ").strip()
            if not line:
                continue
            if line == "/help":
                print("""Commands:
  /llm <text>
  /use <alias> <command to launch>
  /call <alias> <method> [params_json]
  /scenario git_readme <alias_git> <path>
  /history
  /mcp_log
  /exit

Presets:
  /use lol
  /use fs
  /use git
  /use arx
""")
                continue
            if line == "/exit":
                break
            if line == "/history":
                h.print_history()
                continue
            if line == "/mcp_log":
                print(str(LOG_FILE))
                continue
            if line.startswith("/llm "):
                h.do_llm(line[5:].strip())
                continue
            if line.startswith("/use "):
                parts = shlex.split(line)
                if len(parts) == 2:
                    if parts[1] == "lol":
                        h.do_use("lol", default_lol); continue
                    if parts[1] == "fs":
                        h.do_use("fs", default_fs); continue
                    if parts[1] == "git":
                        h.do_use("git", default_git); continue
                    if parts[1] == "arx":
                        h.do_use("arx", default_arx); continue
                    print("Usage: /use <alias> <command to launch>")
                    continue
                if len(parts) >= 3:
                    alias = parts[1]
                    cmd = line.split(alias,1)[1].strip()
                    h.do_use(alias, cmd)
                    continue
                print("Usage: /use <alias> <command to launch>")
                continue
            if line.startswith("/call "):
                parts = shlex.split(line, posix=True)
                if len(parts) < 3:
                    print("Usage: /call <alias> <method> [params_json]")
                    continue
                alias, method = parts[1], parts[2]
                params_json = line.split(method,1)[1].strip() if len(parts) >= 3 else "{}"
                h.do_call(alias, method, params_json)
                continue
            if line.startswith("/scenario "):
                parts = shlex.split(line)
                if len(parts) >= 2 and parts[1] == "git_readme":
                    if len(parts) != 4:
                        print("Usage: /scenario git_readme <alias_git> <repo_path>")
                    else:
                        h.scenario_git_readme(parts[2], parts[3])
                else:
                    print("Unknown scenario.")
                continue
            if line == "/use lol":
                h.do_use("lol", default_lol); continue
            if line == "/use fs":
                h.do_use("fs", default_fs); continue
            if line == "/use git":
                h.do_use("git", default_git); continue
            if line == "/use cal":
                h.do_use("cal", default_cal); continue
            if line == "/use movies":
                h.do_use("movies", default_movies); continue
            print("Unknown command. Type /help.")
    except (KeyboardInterrupt, EOFError):
        print("\n[host] Interrumpido. Usa /exit para salir limpio la próxima vez.")
    finally:
        h.close()

if __name__ == "__main__":
    main()

