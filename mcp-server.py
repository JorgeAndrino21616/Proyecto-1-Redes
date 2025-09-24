import json
import sys
import traceback
import requests
from typing import Dict, Any, Callable, List
import os
import certifi
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class DDragonClient:
    def __init__(self, version="latest", lang="en_US"):
        self.version = version
        self.lang = lang
        self._bootstrapped = False
        self.champions = {}
        self.session = requests.Session()
        allow_insecure = os.getenv("ALLOW_INSECURE_SSL", "").lower() in ("1", "true", "yes")
        if allow_insecure:
            self.session.verify = False
        else:
            self.session.verify = certifi.where()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"])
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.items = {
            "boots_armor": "Plated Steelcaps",
            "boots_mr": "Mercury's Treads",
            "boots_ms": "Boots of Swiftness",
            "anti_heal_armor": "Thornmail",
            "anti_heal_ap": "Morellonomicon",
            "armor": "Dead Man's Plate",
            "mr": "Force of Nature",
            "hp": "Warmog's Armor",
            "ad_core_tank": "Stridebreaker",
            "ad_core_bruiser": "Black Cleaver",
            "ap_core_mage": "Liandry's Torment",
            "tenacity_item": "Silvermere Dawn"
        }
        self.runes = {
            "PRECISION": ["Conqueror", "Triumph", "Legend: Tenacity", "Last Stand"],
            "DOMINATION": ["Electrocute", "Taste of Blood", "Eyeball Collection", "Ultimate Hunter"],
            "RESOLVE": ["Grasp of the Undying", "Demolish", "Second Wind", "Overgrowth"],
            "SORCERY": ["Arcane Comet", "Manaflow Band", "Transcendence", "Scorch"],
            "INSPIRATION": ["Glacial Augment", "Magical Footwear", "Biscuit Delivery", "Cosmic Insight"],
            "SHARDS": ["AS", "Armor", "MR", "HP"]
        }

    def _fetch_json(self, url: str):
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _resolve_version(self, version: str) -> str:
        if version != "latest":
            return version
        try:
            versions = self._fetch_json("https://ddragon.leagueoflegends.com/api/versions.json")
            return versions[0] if isinstance(versions, list) and versions else "15.17.1"
        except Exception:
            return "15.17.1"

        
    def bootstrap(self):
        ver = self._resolve_version(self.version)
        data = self._fetch_json(f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/{self.lang}/champion.json")
        champs = data.get("data", {})
        index: Dict[str, Dict[str, Any]] = {}
        for key, c in champs.items():
            name = c.get("id", key)
            tags = c.get("tags", [])
            info = c.get("info", {})
            spells = c.get("spells", [])
            passive = c.get("passive", {})
            role = tags[0].lower() if tags else "unknown"
            damage = self._infer_damage(tags)
            cc_score = self._estimate_cc(spells, passive)
            tanky = bool(info.get("toughness", 0) >= 5 or "Tank" in tags)
            heals = self._has_heal(spells, passive)
            index[name.lower()] = {
                "damage": damage,
                "tanky": tanky,
                "cc_score": cc_score,
                "heals": heals,
                "role": role
            }
        self.champions = index
        self._bootstrapped = True

    def get_champion(self, name: str) -> Dict[str, Any] | None:
        return self.champions.get(name.lower())

    def _resolve_version(self, version: str) -> str:
        if version != "latest":
            return version
        versions = self._fetch_json("https://ddragon.leagueoflegends.com/api/versions.json")
        return versions[0] if isinstance(versions, list) and versions else "14.10.1"

    def _fetch_json(self, url: str) -> Any:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _infer_damage(self, tags: List[str]) -> str:
        t = set(tags)
        if "Mage" in t or "Support" in t:
            return "AP"
        if "Marksman" in t or "Assassin" in t or "Fighter" in t:
            return "AD"
        if "Tank" in t:
            return "MIX"
        return "MIX"

    def _estimate_cc(self, spells: List[Dict[str, Any]], passive: Dict[str, Any]) -> int:
        text = " ".join([(s.get("tooltip", "") + " " + s.get("description", "")) for s in spells]) + " " + passive.get("description", "")
        text = text.lower()
        hard_cc = ["stun", "root", "snare", "knock up", "knockup", "airborne", "taunt", "fear", "charm", "sleep", "suppression", "silence"]
        soft_cc = ["slow", "cripple"]
        score = 0
        for k in hard_cc:
            if k in text:
                score += 2
        for k in soft_cc:
            if k in text:
                score += 1
        return max(1, min(score, 12))

    def _has_heal(self, spells: List[Dict[str, Any]], passive: Dict[str, Any]) -> bool:
        text = " ".join([(s.get("tooltip", "") + " " + s.get("description", "")) for s in spells]) + " " + passive.get("description", "")
        text = text.lower()
        keys = ["heal", "restores health", "restores hp", "lifesteal", "omnivamp", "regenerate"]
        return any(k in text for k in keys)


def analyze_enemy_comp(dd: DDragonClient, enemy_team: List[str]) -> Dict[str, Any]:
    picks = [str(x).strip().lower() for x in enemy_team]
    ad = ap = 0.0
    cc_total = 0
    tanks, healing, missing = [], [], []
    for c in picks:
        info = dd.get_champion(c)
        if not info:
            missing.append(c)
            continue
        dmg = info["damage"]
        if dmg == "AD":
            ad += 1
        elif dmg == "AP":
            ap += 1
        else:
            ad += 0.5
            ap += 0.5
        cc_total += info["cc_score"]
        if info["tanky"]:
            tanks.append(c)
        if info["heals"]:
            healing.append(c)
    denom = max(ad + ap, 1)
    ad_ratio = round(ad / denom, 2)
    ap_ratio = round(ap / denom, 2)
    if cc_total >= 10:
        cc_level = "HIGH"
    elif cc_total >= 6:
        cc_level = "MEDIUM"
    else:
        cc_level = "LOW"
    result = {
        "ad_ratio": ad_ratio,
        "ap_ratio": ap_ratio,
        "cc_level": cc_level,
        "tanks": tanks,
        "healing_sources": healing,
        "picks": picks
    }
    if missing:
        result["unknown_champions"] = missing
    return result


def suggest_runes(dd: DDragonClient, ally_champion: str, ally_characteristic: str, comp: Dict[str, Any]) -> Dict[str, Any]:
    char = ally_characteristic.upper()
    cc = comp.get("cc_level", "MEDIUM")
    high_cc = cc == "HIGH"
    if char in ("AD", "TANK"):
        primary = ["PRECISION", ["Conqueror", "Triumph", "Legend: Tenacity" if high_cc else "Legend: Alacrity", "Last Stand"]]
        secondary = ["RESOLVE", ["Second Wind" if high_cc else "Demolish", "Overgrowth"]]
        shards = ["AS", "Armor" if comp.get("ad_ratio", 0.5) >= 0.5 else "MR", "HP"]
    else:
        primary = ["SORCERY", ["Arcane Comet", "Manaflow Band", "Transcendence", "Scorch"]]
        secondary = ["RESOLVE" if high_cc else "INSPIRATION",
                     ["Second Wind", "Overgrowth"] if high_cc else ["Biscuit Delivery", "Cosmic Insight"]]
        shards = ["AS", "MR" if comp.get("ap_ratio", 0.5) >= 0.5 else "Armor", "HP"]
    return {
        "ally": ally_champion.lower(),
        "characteristic": char,
        "primary": {"tree": primary[0], "picks": primary[1]},
        "secondary": {"tree": secondary[0], "picks": secondary[1]},
        "shards": shards
    }


def suggest_summoners(dd: DDragonClient, ally_champion: str, ally_characteristic: str, comp: Dict[str, Any]) -> Dict[str, Any]:
    high_cc = comp.get("cc_level") == "HIGH"
    char = ally_characteristic.upper()
    if char in ("AD", "TANK"):
        summs = ["Flash", "Cleanse"] if high_cc else ["Flash", "Ghost"]
    else:
        summs = ["Flash", "Cleanse"] if high_cc else ["Flash", "Barrier"]
    return {"summoners": summs}


def suggest_items(dd: DDragonClient, ally_champion: str, ally_characteristic: str, comp: Dict[str, Any]) -> Dict[str, Any]:
    items = dd.items
    ad_ratio = comp.get("ad_ratio", 0.5)
    ap_ratio = comp.get("ap_ratio", 0.5)
    high_cc = comp.get("cc_level") == "HIGH"
    has_heal = bool(comp.get("healing_sources"))
    boots = items["boots_mr"] if high_cc else (items["boots_armor"] if ad_ratio >= ap_ratio else items["boots_mr"])
    core = []
    if ally_characteristic.upper() in ("AD", "TANK"):
        core.append(items["ad_core_tank"])
        core.append(items["armor"] if ad_ratio >= ap_ratio else items["mr"])
    else:
        core.append(items["ap_core_mage"])
        core.append(items["mr"] if ap_ratio >= ad_ratio else items["armor"])
    situational = []
    if has_heal:
        situational.append(items["anti_heal_armor"] if ad_ratio >= ap_ratio else items["anti_heal_ap"])
    if high_cc:
        situational.append(items["tenacity_item"])
    if abs(ad_ratio - ap_ratio) < 0.2:
        situational.append(items["hp"])
    return {
        "starter": ["Doran's Shield", "Health Potion"],
        "boots": [boots],
        "core": core,
        "situational": situational
    }


STATE: Dict[str, Any] = {
    "dd": None,
    "dd_version": "latest",
    "lang": "en_US",
    "last_comp": None
}

TOOLS: Dict[str, Dict[str, Any]] = {}

def require_dd():
    if STATE["dd"] is None:
        raise RuntimeError("Data Dragon (dd) is not initialized. Call fetch_static_data first.")
    return STATE["dd"]

def tool(name: str, description: str, params_schema: Dict[str, Any]):
    def deco(fn: Callable[[Dict[str, Any]], Any]):
        TOOLS[name] = {"name": name, "description": description, "input_schema": params_schema, "run": fn}
        return fn
    return deco


@tool(
    name="analyze_enemies",
    description="Analyze enemy composition (AD/AP ratios, CC level, tanks, healing) and store it as 'last_comp'.",
    params_schema={
        "type":"object",
        "properties":{"enemy_team":{"type":"array","items":{"type":"string"},"minItems":5,"maxItems":5}},
        "required":["enemy_team"],
        "additionalProperties":False
    }
)
def _tool_analyze_enemies(params: Dict[str, Any]):
    dd = require_dd()
    enemies = [str(e).strip().lower() for e in params["enemy_team"]]
    comp = analyze_enemy_comp(dd, enemies)
    STATE["last_comp"] = comp
    return comp


@tool(
    name="suggest_runes",
    description="Suggest runes for the ally. If 'comp' is omitted, uses 'last_comp'.",
    params_schema={
        "type":"object",
        "properties":{
            "ally_champion":{"type":"string"},
            "ally_characteristic":{"type":"string","enum":["AD","AP","TANK"]},
            "comp":{"type":"object"}
        },
        "required":["ally_champion","ally_characteristic"],
        "additionalProperties":False
    }
)
def _tool_suggest_runes(params: Dict[str, Any]):
    dd = require_dd()
    comp = params.get("comp") or STATE.get("last_comp")
    if not comp:
        raise RuntimeError("No 'comp' provided and no 'last_comp' stored. Run analyze_enemies first.")
    return suggest_runes(dd, params["ally_champion"], params["ally_characteristic"], comp)


@tool(
    name="suggest_summoners",
    description="Suggest summoner spells for the ally. If 'comp' is omitted, uses 'last_comp'.",
    params_schema={
        "type":"object",
        "properties":{
            "ally_champion":{"type":"string"},
            "ally_characteristic":{"type":"string","enum":["AD","AP","TANK"]},
            "comp":{"type":"object"}
        },
        "required":["ally_champion","ally_characteristic"],
        "additionalProperties":False
    }
)
def _tool_suggest_summoners(params: Dict[str, Any]):
    dd = require_dd()
    comp = params.get("comp") or STATE.get("last_comp")
    if not comp:
        raise RuntimeError("No 'comp' provided and no 'last_comp' stored. Run analyze_enemies first.")
    return suggest_summoners(dd, params["ally_champion"], params["ally_characteristic"], comp)


@tool(
    name="suggest_items",
    description="Suggest items for the ally. If 'comp' is omitted, uses 'last_comp'.",
    params_schema={
        "type":"object",
        "properties":{
            "ally_champion":{"type":"string"},
            "ally_characteristic":{"type":"string","enum":["AD","AP","TANK"]},
            "comp":{"type":"object"}
        },
        "required":["ally_champion","ally_characteristic"],
        "additionalProperties":False
    }
)
def _tool_suggest_items(params: Dict[str, Any]):
    dd = require_dd()
    comp = params.get("comp") or STATE.get("last_comp")
    if not comp:
        raise RuntimeError("No 'comp' provided and no 'last_comp' stored. Run analyze_enemies first.")
    return suggest_items(dd, params["ally_champion"], params["ally_characteristic"], comp)


@tool(
    name="plan_build",
    description="One-shot planner: given ally champion/characteristic and 5 enemies, analyze and return items, runes and summoners.",
    params_schema={
        "type":"object",
        "properties":{
            "ally_champion":{"type":"string"},
            "ally_characteristic":{"type":"string","enum":["AD","AP","TANK"]},
            "enemy_team":{"type":"array","items":{"type":"string"},"minItems":5,"maxItems":5}
        },
        "required":["ally_champion","ally_characteristic","enemy_team"],
        "additionalProperties":False
    }
)
def _tool_plan_build(params: Dict[str, Any]):
    dd = require_dd()
    enemies = [str(e).strip().lower() for e in params["enemy_team"]]
    comp = analyze_enemy_comp(dd, enemies)
    STATE["last_comp"] = comp
    ally = params["ally_champion"]
    char = params["ally_characteristic"]
    return {
        "comp": comp,
        "items": suggest_items(dd, ally, char, comp),
        "runes": suggest_runes(dd, ally, char, comp),
        "summoners": suggest_summoners(dd, ally, char, comp)
    }


def rpc_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"serverInfo": {"name": "lol-champion-builder", "version": "0.3.0"}, "capabilities": {"tools": True}}

def rpc_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"tools": [{"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]} for t in TOOLS.values()]}

def rpc_tools_call(params: Dict[str, Any]) -> Any:
    name = params.get("name")
    args = params.get("arguments") or {}
    if name not in TOOLS:
        raise RuntimeError(f"Tool not found: {name}")
    return TOOLS[name]["run"](args)

def rpc_fetch_static_data(params: Dict[str, Any]) -> Dict[str, Any]:
    version = params.get("ddragon_version") or "latest"
    lang = params.get("lang") or "en_US"
    STATE["dd_version"] = version
    STATE["lang"] = lang
    dd = DDragonClient(version=version, lang=lang)
    dd.bootstrap()
    STATE["dd"] = dd
    return {"ok": True, "version": version, "lang": lang}


HANDLERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "initialize": rpc_initialize,
    "tools/list": rpc_tools_list,
    "tools/call": rpc_tools_call,
    "fetch_static_data": rpc_fetch_static_data
}

def _make_result(id_, result=None, error=None):
    if error is not None:
        return {"jsonrpc":"2.0","id":id_,"error":{"code": -32000, "message": str(error)}}
    return {"jsonrpc":"2.0","id":id_,"result": result}

def main():
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                method = req.get("method")
                params = req.get("params") or {}
                id_ = req.get("id")
                if method not in HANDLERS:
                    raise RuntimeError(f"Unknown method: {method}")
                result = HANDLERS[method](params)
                sys.stdout.write(json.dumps(_make_result(id_, result=result)) + "\n")
                sys.stdout.flush()
            except Exception as e:
                tb = traceback.format_exc()
                sys.stdout.write(json.dumps(_make_result(req.get("id") if 'req' in locals() else None, error=f"{e}\n{tb}")) + "\n")
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
