import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"


def query_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    data = response.json()

    # ✅ SAFE handling for different Ollama versions
    if "response" in data:
        return data["response"]

    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]

    raise ValueError(f"Unexpected Ollama response format: {data}")
