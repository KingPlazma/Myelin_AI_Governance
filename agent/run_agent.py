import os
import sys
import subprocess

# Ensure we are in the agent directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run():
    print("="*80)
    print(" MYELIN SENTINEL 24/7 AGENT - LAUNCHER ".center(80, "="))
    print("="*80)
    print("\n[DAY 1 & 2 FEATURES ACTIVE]")
    print("1. OpenAI-Compatible Proxy (Port 9000)")
    print("2. Integrated 5-Pillar Governance Engine")
    print("3. Autonomous Remediation (PII Redaction & Toxicity Blocking)")
    print("\nStarting Proxy Server...")
    
    try:
        # Run using uvicorn
        subprocess.run(["uvicorn", "proxy_server:app", "--host", "0.0.0.0", "--port", "9000"])
    except KeyboardInterrupt:
        print("\nStopping Myelin Agent...")
    except Exception as e:
        print(f"Error starting agent: {e}")

if __name__ == "__main__":
    run()
