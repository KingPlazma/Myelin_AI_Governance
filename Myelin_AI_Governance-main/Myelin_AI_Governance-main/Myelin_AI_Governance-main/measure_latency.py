import requests
import time

BOT_URL = "http://localhost:8001/chat"
AUDIT_URL = "http://localhost:8001/audit"

def test_latency():
    print("\n--- MEASURING LATENCY OPTIMIZATION ---")
    
    payload = {"message": "What time is lunch?"}
    
    # 1. Test Chat Response Time (Bot Text Only)
    start_time = time.time()
    try:
        chat_resp = requests.post(BOT_URL, json=payload, timeout=120)
        chat_data = chat_resp.json()
        chat_time = time.time() - start_time
        print(f"✅ BOT TEXT RECEIVED: {chat_time:.2f} seconds")
        print(f"BOT RESPONSE: {chat_data['bot_response']}")
        
        # 2. Test Audit Latency (Background Task)
        start_audit = time.time()
        audit_payload = {
            "user_message": chat_data["user_message"],
            "bot_response": chat_data["bot_response"],
            "context": chat_data["context"]
        }
        audit_resp = requests.post(AUDIT_URL, json=audit_payload, timeout=120)
        audit_data = audit_resp.json()
        audit_time = time.time() - start_audit
        print(f"✅ MYELIN AUDIT RECEIVED: {audit_time:.2f} seconds (Parallel Pillars)")
        
        # Check if audit worked
        fact_score = audit_data.get("pillars", {}).get("factual", {}).get("final_score", "N/A")
        print(f"Audit Status: {audit_data.get('overall', {}).get('decision')}")
        print(f"Factual Score: {fact_score}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Wait for servers to be fully ready
    print("Waiting for servers to settle...")
    time.sleep(5) 
    test_latency()
