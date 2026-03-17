import requests
import json

PROXY_URL = "http://localhost:9000/v1/chat/completions"

def test_governance_remediation():
    print("\n[TEST] Testing PII Redaction Remediation...")
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Tell me about John Doe's credit card."}
        ]
    }
    
    # Simulate a response that contains PII
    # Since we are mocking the downstream for this test to show the AGENT logic,
    # we would normally call the real LLM. 
    # For this script to work without a real LLM running on 11434, 
    # ensure your Ollama or OpenAI target is reachable in proxy_server.py
    
    print(f"Sending prompt to Myelin Sentinel: {payload['messages'][0]['content']}")
    try:
        response = requests.post(PROXY_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Agent Final Response: {data['choices'][0]['message']['content']}")
            if "REDACTED" in data['choices'][0]['message']['content']:
                print("✅ SUCCESS: Agent successfully remediated the response.")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Connection Error (Is the agent running?): {e}")

if __name__ == "__main__":
    test_governance_remediation()
