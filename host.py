# Para correrlo, correr antes los API con una key de GROQ, en GROQ_API_KEY

import os, sys
from llm_client import ask_llm
from mcp_client import start_mcp, call_mcp

def ask_input_nonempty(prompt):
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Input cannot be empty.")

def parse_enemies(s):
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) != 5:
        print("You must enter exactly 5 enemy champions separated by commas. Example: Garen, Maokai, Ahri, Jinx, Lulu")
        return None
    return parts

def build_matchup_text(ally_champ, characteristic, enemies):
    return f"I want to play {ally_champ} {characteristic} against {', '.join(enemies)}"

def main():
    here = os.path.dirname(__file__)
    server = (
        os.path.join(here, "mcp-server.py")
        if os.path.exists(os.path.join(here, "mcp-server.py"))
        else os.path.join(here, "mcp_server.py")
    )
    if not os.path.exists(server):
        print(f"Could not find MCP server script: {server}")
        sys.exit(1)

    lol_proc = start_mcp([sys.executable, server])

    try:
        print("\n=== League of Legends Champion Builder ===")
        ally = ask_input_nonempty("Your champion: ")
        characteristic = ask_input_nonempty("Characteristic: ")

        enemies = None
        while enemies is None:
            s = ask_input_nonempty("Enter 5 enemy champions separated by commas: ")
            enemies = parse_enemies(s)

        ddragon_version = "latest"
        lang = "en_US"  

        print("\nFetching static data from DDragon...")
        print(call_mcp(lol_proc, "fetch_static_data", {
            "ddragon_version": ddragon_version,
            "lang": lang
        }))

        print("Setting up the matchup...")
        text = build_matchup_text(ally, characteristic, enemies)
        print(call_mcp(lol_proc, "matchup", {"text": text}))

        print("Analyzing enemy composition...")
        print(call_mcp(lol_proc, "analyze_enemies", {}))

        print("Suggested RUNES:")
        print(call_mcp(lol_proc, "suggest_runes", {}))

        print("Suggested SUMMONER SPELLS:")
        print(call_mcp(lol_proc, "suggest_summoners", {}))

        print("Suggested ITEMS:")
        print(call_mcp(lol_proc, "suggest_items", {}))

        print("\nDone.")
    finally:
        lol_proc.terminate()

if __name__ == "__main__":
    main()


