# Para el servidor

import os, sys, json, traceback
from typing import Any, Dict

from groq import parse_intent_text
from client import DDragonClient
from comp_analyzer import analyze_enemy_comp
from build import suggest_runes, suggest_summoners, suggest_items

STATE = {
    "matchup": {
        "ally_champion": None,
        "ally_characteristic": None,  # "AD" | "AP" | "TANK"
        "enemy_team": []
    },
    "dd": None,   # DDragonClient
    "dd_version": None,
    "lang": os.getenv("DDRAGON_LANG", "en_US")
}

def make_result(id_, result=None, error=None):
    if error:
        return {"jsonrpc":"2.0", "id": id_, "error": {"code": -32000, "message": str(error)}}
    return {"jsonrpc":"2.0", "id": id_, "result": result}

def rpc_set_matchup(params: Dict[str, Any]) -> Dict[str, Any]:
    if "text" in params:
        data = parse_intent_text(params["text"])
        STATE["matchup"].update(data)
    else:
        STATE["matchup"]["ally_champion"] = params["ally_champion"].lower()
        STATE["matchup"]["ally_characteristic"] = params["ally_characteristic"].upper()
        STATE["matchup"]["enemy_team"] = [e.lower() for e in params["enemy_team"]]
    return {"ok": True, "matchup": STATE["matchup"]}

def rpc_fetch_static_data(params: Dict[str, Any]) -> Dict[str, Any]:
    if "lang" in params:
        STATE["lang"] = params["lang"]
    dd = DDragonClient(lang=STATE["lang"])
    ver = dd.ensure_latest(params.get("ddragon_version", "latest"))
    STATE["dd"] = dd
    STATE["dd_version"] = ver
    return {"ok": True, "version": ver, "lang": STATE["lang"]}

def rpc_analyze_enemy_comp(params: Dict[str, Any]) -> Dict[str, Any]:
    if not STATE["dd"]: raise RuntimeError("Call fetch_static_data first.")
    if not STATE["matchup"]["enemy_team"]: raise RuntimeError("Set enemy_team with set_matchup.")
    return analyze_enemy_comp(STATE["dd"], STATE["matchup"]["enemy_team"])

def rpc_suggest_runes(params: Dict[str, Any]) -> Dict[str, Any]:
    mu = STATE["matchup"]
    comp = analyze_enemy_comp(STATE["dd"], mu["enemy_team"])
    return suggest_runes(STATE["dd"], mu["ally_champion"], mu["ally_characteristic"], comp)

def rpc_suggest_summoners(params: Dict[str, Any]) -> Dict[str, Any]:
    mu = STATE["matchup"]
    comp = analyze_enemy_comp(STATE["dd"], mu["enemy_team"])
    return suggest_summoners(mu["ally_champion"], mu["ally_characteristic"], comp)

def rpc_suggest_items(params: Dict[str, Any]) -> Dict[str, Any]:
    mu = STATE["matchup"]
    comp = analyze_enemy_comp(STATE["dd"], mu["enemy_team"])
    return suggest_items(STATE["dd"], mu["ally_champion"], mu["ally_characteristic"], comp)


HANDLERS = {
    "matchup": rpc_set_matchup,
    "fetch_static_data": rpc_fetch_static_data,
    "analyze_enemies": rpc_analyze_enemy_comp,
    "suggest_runes": rpc_suggest_runes,
    "suggest_summoners": rpc_suggest_summoners,
    "suggest_items": rpc_suggest_items,
}

def main():
    while True:
        line = sys.stdin.readline()
        if not line: break
        try:
            req = json.loads(line); method = req.get("method"); params = req.get("params", {}) or {}; id_ = req.get("id")
            if method not in HANDLERS:
                resp = make_result(id_, error=f"Method not found: {method}")
            else:
                resp = make_result(id_, result=HANDLERS[method](params))
        except Exception as e:
            rid = req.get("id") if 'req' in locals() else None
            resp = make_result(rid, error=str(e))
        sys.stdout.write(json.dumps(resp) + "\n"); sys.stdout.flush()

if __name__ == "__main__":
    main()
