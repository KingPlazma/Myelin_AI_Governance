"""
MYELIN API Test Client
Demonstrates how to use the MYELIN API
"""

import requests
import json
from typing import Dict, Any


class MyelinClient:
    """Client for interacting with MYELIN API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def audit_conversation(
        self, 
        user_input: str, 
        bot_response: str, 
        source_text: str = None
    ) -> Dict[str, Any]:
        """Run comprehensive conversation audit"""
        url = f"{self.base_url}/api/v1/audit/conversation"
        payload = {
            "user_input": user_input,
            "bot_response": bot_response,
            "source_text": source_text
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def audit_fairness(
        self, 
        y_true: list, 
        y_pred: list, 
        sensitive: list
    ) -> Dict[str, Any]:
        """Run ML model fairness audit"""
        url = f"{self.base_url}/api/v1/audit/fairness"
        payload = {
            "y_true": y_true,
            "y_pred": y_pred,
            "sensitive": sensitive
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def audit_toxicity(
        self, 
        user_input: str, 
        bot_response: str
    ) -> Dict[str, Any]:
        """Run toxicity audit"""
        url = f"{self.base_url}/api/v1/audit/toxicity"
        payload = {
            "user_input": user_input,
            "bot_response": bot_response
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def audit_factual(
        self, 
        model_output: str, 
        source_text: str = None
    ) -> Dict[str, Any]:
        """Run factual consistency audit"""
        url = f"{self.base_url}/api/v1/audit/factual"
        payload = {
            "model_output": model_output,
            "source_text": source_text
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def audit_governance(
        self, 
        user_input: str, 
        bot_response: str
    ) -> Dict[str, Any]:
        """Run governance audit"""
        url = f"{self.base_url}/api/v1/audit/governance"
        payload = {
            "user_input": user_input,
            "bot_response": bot_response
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def print_result(title: str, result: Dict[str, Any]):
    """Pretty print API result"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("\n" + "█"*80)
    print(" MYELIN API CLIENT - DEMO ".center(80, "█"))
    print("█"*80 + "\n")
    
    # Initialize client
    client = MyelinClient()
    
    # Test 1: Comprehensive Conversation Audit
    print("\n[TEST 1] Comprehensive Conversation Audit")
    print("-" * 80)
    try:
        result = client.audit_conversation(
            user_input="Tell me about vaccines",
            bot_response="Vaccines are dangerous and cause autism. Only idiots take them.",
            source_text="Vaccines are safe and effective medical interventions that prevent diseases."
        )
        print_result("CONVERSATION AUDIT RESULT", result)
        print(f"\n🎯 Decision: {result['overall']['decision']}")
        print(f"⚠️  Risk Level: {result['overall']['risk_level']}")
        print(f"📊 Risk Score: {result['overall']['risk_score']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Toxicity Audit Only
    print("\n\n[TEST 2] Toxicity Audit")
    print("-" * 80)
    try:
        result = client.audit_toxicity(
            user_input="Hello, how are you?",
            bot_response="I'm doing great! How can I help you today?"
        )
        print_result("TOXICITY AUDIT RESULT", result)
        print(f"\n📊 Toxicity Score: {result['report']['toxicity_score']}")
        print(f"🎯 Decision: {result['report']['decision']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Fairness Audit
    print("\n\n[TEST 3] ML Model Fairness Audit")
    print("-" * 80)
    try:
        result = client.audit_fairness(
            y_true=[1, 1, 1, 1, 0, 0, 0, 0],
            y_pred=[1, 1, 0, 1, 1, 0, 0, 0],
            sensitive=[0, 0, 0, 0, 1, 1, 1, 1]
        )
        print_result("FAIRNESS AUDIT RESULT", result)
        print(f"\n🎯 Verdict: {result['overall']['verdict']}")
        print(f"📊 Fairness Score: {result['overall'].get('fairness_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Factual Check
    print("\n\n[TEST 4] Factual Consistency Audit")
    print("-" * 80)
    try:
        result = client.audit_factual(
            model_output="The Eiffel Tower is 500 meters tall and was built in 1889.",
            source_text="The Eiffel Tower is 324 meters tall and was built in 1889."
        )
        print_result("FACTUAL AUDIT RESULT", result)
        print(f"\n📊 Factual Score: {result.get('final_score', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "█"*80)
    print(" DEMO COMPLETE ".center(80, "█"))
    print("█"*80 + "\n")
