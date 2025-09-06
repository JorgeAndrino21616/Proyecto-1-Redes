
import json, time, subprocess, pathlib

LOG_PATH = pathlib.Path("./logs"); LOG_PATH.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_PATH / "mcp.log"

def log_io(direction, payload):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(f"{ts} {direction} {json.dumps(payload, ensure_ascii=False)}\n")

def start_mcp(cmd):
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

def call_mcp(proc, method, params):
    req = {"jsonrpc":"2.0","id":int(time.time()*1000),"method":method,"params":params}
    log_io("->", req)
    proc.stdin.write(json.dumps(req)+"\n"); proc.stdin.flush()
    line = proc.stdout.readline()
    resp = json.loads(line)
    log_io("<-", resp)
    if "error" in resp: raise RuntimeError(resp["error"]["message"])
    return resp["result"]
