#!/usr/bin/env python3
"""
Test script for the enhanced Myelin chatbot demo.
Tests the backend functionality without running the full Streamlit app.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_backend_imports():
    """Test that backend imports work correctly."""
    try:
        import backend
        print("✅ Backend imports successfully")
        return True
    except Exception as e:
        print(f"❌ Backend import failed: {e}")
        return False

def test_bot_response_logic():
    """Test the enhanced bot response logic."""
    try:
        from backend import build_hiring_bot_response

        # Test a regular greeting
        result = build_hiring_bot_response("hello")
        assert "response" in result
        assert "category" in result
        assert result["category"] == "greeting"
        print("✅ Bot response logic works for greetings")

        # Test a refund request
        result = build_hiring_bot_response("I want a refund")
        assert "response" in result
        assert "category" in result
        assert "refund" in result["category"]
        print("✅ Bot response logic works for refunds")

        # Test a delivery issue
        result = build_hiring_bot_response("my package is late")
        assert "response" in result
        assert "delivery" in result["response"].lower()
        print("✅ Bot response logic works for delivery issues")

        print("✅ Bot response logic tests passed")
        return True

    except Exception as e:
        print(f"❌ Bot response logic test failed: {e}")
        return False

def test_demo_scenarios():
    """Test that demo scenarios are properly defined."""
    try:
        from backend import DEMO_SCENARIOS

        required_keys = ["prompt", "description", "expected_decision", "showcase_pillar"]
        for scenario_name, scenario_data in DEMO_SCENARIOS.items():
            for key in required_keys:
                assert key in scenario_data, f"Missing {key} in {scenario_name}"
            print(f"✅ Scenario '{scenario_name}' is properly configured")

        print("✅ All demo scenarios are valid")
        return True

    except Exception as e:
        print(f"❌ Demo scenarios test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Enhanced Myelin Chatbot Demo")
    print("=" * 50)

    tests = [
        test_backend_imports,
        test_bot_response_logic,
        test_demo_scenarios,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The enhanced chatbot demo is ready.")
        print("\nTo run the demo:")
        print("1. Start the backend: uvicorn backend:app --host 127.0.0.1 --port 8010 --reload")
        print("2. Start the frontend: streamlit run frontend.py")
        print("3. Open http://localhost:8501 in your browser")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())