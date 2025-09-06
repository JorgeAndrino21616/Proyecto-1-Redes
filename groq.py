# Para establecer como funciona groq

import os, json, requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")  

SYSTEM = """You are a strict intent extractor for League of Legends.
Input: free text like "I want to play Darius tank against Garen, Maokai, Ahri, Jinx, Lulu".
Output JSON:
{"ally_champion":"<string>","ally_characteristic":"AD|AP|TANK","enemy_team":["<5 champs>"]}"""

def _fallback(text: str):
    t = text.lower()
    char = "TANK" if ("tank" in t) else ("AP" if " ap" in t else "AD")
    ally = re.findall(r"(?:play|use)\s+([a-zA-Z'\\.]+)", t)
    ally = ally[0] if ally else "darius"
    enemies = []
    if "against" in t or "vs" in t:
        enemies = [x for x in re.split(r"[,\s]+", t.split("against",1)[1]) if x.isalpha()]
    if len(enemies) < 5:
        enemies = (enemies + ["garen","maokai","ahri","jinx","lulu"])[:5]
    return {"ally_champion": ally, "ally_characteristic": char, "enemy_team": enemies[:5]}

def parse_intent_text(text: str):
    if not GROQ_API_KEY:
        return _fallback(text)
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {"model": MODEL, "temperature": 0, "messages": [
        {"role":"system","content":SYSTEM},
        {"role":"user","content":text}
    ]}
    r = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m: return _fallback(text)
        data = json.loads(m.group(0))
    data["ally_champion"] = data["ally_champion"].lower()
    data["ally_characteristic"] = data["ally_characteristic"].upper()
    data["enemy_team"] = [e.lower() for e in data.get("enemy_team", [])][:5]
    return data
