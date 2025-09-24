
Se puede utilizar el bot de Groq con /llm y se usa lol para utilizar el lol-champion-builder

Ejemplo de funcionamiento:

=== Host MCP — type /help for commands ===
```> /use lol
> /call lol initialize {}
{
  "serverInfo": {
    "name": "lol-champion-builder",
    "version": "0.3.0"
  },
  "capabilities": {
    "tools": true
  }
}
> /call lol fetch_static_data {"ddragon_version":"latest","lang":"en_US"}
{
  "ok": true,
  "version": "latest",
  "lang": "en_US"
}
> /call lol tools/call {"name":"plan_build","arguments":{"ally_champion":"gnar","ally_characteristic":"TANK","enemy_team":["morgana","lulu","ryze","garen","aatrox"]}}
{
  "comp": {
    "ad_ratio": 0.4,
    "ap_ratio": 0.6,
    "cc_level": "LOW",
    "tanks": [
      "garen"
    ],
    "healing_sources": [],
    "picks": [
      "morgana",
      "lulu",
      "ryze",
      "garen",
      "aatrox"
    ]
  },
  "items": {
    "starter": [
      "Doran's Shield",
      "Health Potion"
    ],
    "boots": [
      "Mercury's Treads"
    ],
    "core": [
      "Stridebreaker",
      "Force of Nature"
    ],
    "situational": [
      "Warmog's Armor"
    ]
  },
  "runes": {
    "ally": "gnar",
    "characteristic": "TANK",
    "primary": {
      "tree": "PRECISION",
      "picks": [
        "Conqueror",
        "Triumph",
        "Legend: Alacrity",
        "Last Stand"
      ]
    },
    "secondary": {
      "tree": "RESOLVE",
      "picks": [
        "Demolish",
        "Overgrowth"
      ]
    },
    "shards": [
      "AS",
      "MR",
      "HP"
    ]
  },
  "summoners": {
    "summoners": [
      "Flash",
      "Ghost"
    ]
  }
}```
