Myelin Enhanced Governance Demo

Purpose:
This enhanced demo showcases Myelin's comprehensive AI governance capabilities through an interactive support chatbot. Every user message triggers real-time auditing across all 5 governance pillars, with detailed feedback and intervention capabilities.

Flow:
User Prompt → Enhanced Frontend (Streamlit)
    ↓
Demo Backend (FastAPI) → Myelin Agent API
    ↓
LLM Response + Comprehensive Governance Audit
    ↓
Response + Real-time Audit Feedback + Database Storage

What this demonstrates:
- ✅ Real-time governance auditing across 5 pillars (Toxicity, Bias, Factual, Governance, Fairness)
- ✅ Interactive demo scenarios for testing specific governance capabilities
- ✅ Comprehensive audit logging to Firebase and local JSON backup
- ✅ Professional vs. naive response modes
- ✅ Real-time risk assessment and intervention feedback
- ✅ Conversation session tracking
- ✅ Governance statistics and compliance metrics

Enhanced Features:
🎯 Demo Scenarios: Pre-built prompts that showcase specific governance pillars
📊 Real-time Audit Dashboard: Live governance feedback for every response
🎨 Enhanced UI: Modern chat interface with governance visualizations
📈 Analytics: Compliance metrics and governance statistics
🔄 Session Tracking: Conversation context and audit trails
🛡️ Dual Modes: Professional responses vs. naive mode (shows violations)

Setup:
1. pip install -r requirements.txt
2. Ensure Myelin Agent is running on http://127.0.0.1:9000
3. Ensure Ollama or your LLM provider is accessible
4. Start demo backend:
   uvicorn backend:app --host 127.0.0.1 --port 8010 --reload
5. Start enhanced frontend:
   streamlit run frontend.py

Environment Variables:
- DEMO_BACKEND_URL: Backend URL (default: http://127.0.0.1:8010)
- MYELIN_REPO_ROOT: Path to Myelin repository
- MYELIN_AGENT_HEALTH_URL: Myelin agent health check URL
- FIREBASE_CREDENTIALS_JSON: Path to Firebase credentials
- FIREBASE_DATABASE_ID: Firebase database ID
- NAIVE_DEMO_MODE: true/false - Show problematic responses for demo
- SHOW_GOVERNANCE_INTERVENTION: true/false - Enable governance feedback

Demo Scenarios:
1. Safe Greeting - Basic compliance check
2. Refund Request - Policy compliance
3. Privacy Violation - Governance pillar demo
4. Toxic Request - Toxicity detection
5. Biased Request - Fairness analysis
6. Factual Misinformation - Factual checking
7. Harassment Scenario - Professional response handling

API Endpoints:
- POST /chat - Send message and get audited response
- GET /demo/scenarios - Get available demo scenarios
- GET /audits/recent - Get recent audit logs
- GET /audits/summary - Get governance statistics
- GET /demo/knowledge - Get bot knowledge base
- GET /health - Health check

Files:
- backend.py → Enhanced FastAPI backend with comprehensive auditing
- frontend.py → Modern Streamlit UI with real-time governance feedback
- audit_logs.json → Local audit trail backup
- requirements.txt → Python dependencies

Testing:
1. Start both backend and frontend
2. Try different demo scenarios from the sidebar
3. Switch between Professional and Naive modes
4. Monitor real-time audit feedback
5. Check governance statistics in the sidebar
6. Review audit logs for detailed analysis

Governance Pillars Demonstrated:
🔴 Toxicity: Harmful, abusive, or inappropriate content
🔵 Bias: Unfair discrimination based on protected characteristics
🟣 Factual: Accuracy and truthfulness verification
🟢 Governance: Policy compliance and organizational rules
🟡 Fairness: Equitable treatment and resource allocation

The demo shows how Myelin provides comprehensive AI governance, ensuring safe, compliant, and ethical AI interactions in real-time.
