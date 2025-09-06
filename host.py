
import os
from llm_client import ask_llm
from mcp_client import start_mcp, call_mcp

SESSION = []

def chat_user(msg):
    SESSION.append({"role":"user","content":msg})
    ans = ask_llm(SESSION)
    SESSION.append({"role":"assistant","content":ans})
    return ans

def main():
    lol_proc = start_mcp(["python","mcp_server.py"])

    print("LLM:", chat_user("What is League of Legends?"))
    print("LLM (context):", chat_user("And what is the 'tank' role in general?"))

    print("\n== lol-build-advisor ==")
    print(call_mcp(lol_proc, "fetch_static_data", {"ddragon_version":"latest","lang":"en_US"}))
    print(call_mcp(lol_proc, "set_matchup", {
        "text": "I want to play Darius tank against Garen, Maokai, Ahri, Jinx, and Lulu"
    }))
    print(call_mcp(lol_proc, "analyze_enemy_comp", {}))
    print(call_mcp(lol_proc, "suggest_runes", {}))
    print(call_mcp(lol_proc, "suggest_summoners", {}))
    print(call_mcp(lol_proc, "suggest_items", {}))
    print(call_mcp(lol_proc, "report", {"out_dir":"./reports/demo"}))

    lol_proc.terminate()

if __name__ == "__main__":
    main()
