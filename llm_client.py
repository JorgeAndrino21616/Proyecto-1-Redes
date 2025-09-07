import os, requests

API_KEY = ""
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_llm(messages, max_tokens=512, temperature=0.3):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    r = requests.post(URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
