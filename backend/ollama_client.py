import requests

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL_NAME = "granite3.3:2b"   # ✅ set your Ollama model here

def ask_ollama(prompt: str) -> str:
    """
    Sends a prompt to the Ollama model and returns the response.
    """
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "⚠️ No response from Ollama")
    except Exception as e:
        return f"❌ Ollama Error: {e}"
