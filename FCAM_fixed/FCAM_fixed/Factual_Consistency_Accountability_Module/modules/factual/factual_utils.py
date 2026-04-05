import requests
import re
import math

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:mini"

# --- TRANSFORMER FALLBACK LOGIC ---
_transformer = None
_has_transformer = False

try:
    # Try importing strict dependencies
    import numpy as np
    from sentence_transformers import SentenceTransformer
    
    # Initialize lightweight model
    # We use a try-except block here too in case download fails/access denied
    try:
        _transformer = SentenceTransformer("all-MiniLM-L6-v2")
        _has_transformer = True
    except Exception as e:
        print(f"Warning: SentenceTransformer found but failed to load: {e}")
        _has_transformer = False

except ImportError:
    pass

def query_ollama(prompt):
    """
    Queries local Ollama instance.
    """
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code != 200:
            return ""
            
        data = response.json()

        # ✅ SAFE handling for different Ollama versions
        if "response" in data:
            return data["response"]

        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
            
        return ""
    except:
        return "" # Fail gracefully if Ollama is down

def calculate_similarity(text1, text2):
    """
    Calculates semantic similarity between two texts.
    Uses SentenceTransformer if available, otherwise falls back to Jaccard similarity.
    """
    if _has_transformer and _transformer:
        try:
            emb = _transformer.encode([text1, text2])
            # Cosine similarity
            return float(np.dot(emb[0], emb[1]) / (np.linalg.norm(emb[0]) * np.linalg.norm(emb[1])))
        except:
             pass # Fallback if encoding fails
             
    # --- FALLBACK: Jaccard Similarity ---
    # Tokenize simple words
    def get_tokens(text):
        return set(re.findall(r'\w+', text.lower()))
    
    s1 = get_tokens(text1)
    s2 = get_tokens(text2)
    
    if not s1 or not s2: 
        return 0.0
        
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    
    return float(intersection) / float(union)
