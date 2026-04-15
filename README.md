# MYELIN - AI Governance and Alignment Auditor



## 🎯 Overview

**MYELIN** is a comprehensive AI governance middleware that audits AI-generated content across five critical pillars:

1. **🔍 Fairness** - Ensures equitable outcomes in ML predictions
2. **⚖️ Bias** - Detects gender, racial, religious, and socioeconomic biases
3. **✓ Factual Check (FCAM)** - Validates factual consistency and detects hallucinations
4. **⚠️ Toxicity** - Identifies toxic, harmful, and unsafe content
5. **🛡️ Governance** - Ensures compliance with organizational policies

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MYELIN ORCHESTRATOR                            │
│                       (Unified Integration Layer)                       │
└────────────┬────────────┬────────────┬────────────┬────────────┬────────┘
             │            │            │            │            │
    ┌────────▼───┐  ┌─────▼────┐  ┌────▼─────┐  ┌───▼─────┐  ┌───▼────────┐
    │  Fairness  │  │   Bias   │  │ Factual  │  │Toxicity │  │ Governance │
    │   Pillar   │  │  Pillar  │  │  Check   │  │ Pillar  │  │   Pillar   │
    │            │  │          │  │  (FCAM)  │  │         │  │            │
    └────────────┘  └──────────┘  └──────────┘  └─────────┘  └────────────┘
             │            │            │            │            │
             └────────────┴────────────┴────────────┴────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   FastAPI Server   │
                    │  (REST API Layer)  │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Frontend Demo UI  │
                    └────────────────────┘
```

## 📦 Project Structure

```
myelin_integrated/
├── orchestrator/                    # 🎯 NEW: Unified orchestrator
│   ├── __init__.py
│   ├── myelin_orchestrator.py      # Core integration logic
│   ├── api_server.py               # FastAPI REST API
│   ├── test_client.py              # Python API client example
│   └── requirements_api.txt        # API dependencies
│
├── Myelin_Fairness_Pillar_RICH_FINAL/
│   ├── ensemble.py                 # Fairness ensemble manager
│   ├── main.py                     # Fairness pillar entry point
│   └── rules/                      # Fairness detection rules
│
├── FCAM_fixed/
│   └── FCAM_fixed/
│       └── Factual_Consistency_Accountability_Module/
│           ├── main.py             # FCAM entry point
│           └── modules/
│               └── factual/
│                   ├── ensemble_manager.py
│                   └── rules/      # 20 factual verification rules
│
├── Toxicity/
│   └── Toxicity/
│       ├── main.py                 # Toxicity pillar entry point
│       └── modules/
│           └── toxicity/
│               ├── ensemble_manager.py
│               └── rules/          # Toxicity detection rules
│
├── Governance_Project/
│   └── Governance_Project/
│       ├── main.py                 # Governance pillar entry point
│       └── modules/
│           └── governance/
│               ├── ensemble_manager.py
│               └── rules/          # Governance compliance rules
│
└── frontend/                        # 🎨 UPDATED: Enhanced frontend
    ├── index.html                  # Landing page with live demo
    ├── style.css                   # Main styles
    ├── demo.css                    # Demo section styles
    ├── script.js                   # Particle animations
    ├── demo.js                     # API integration logic
    └── img/                        # Images and assets
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Install API dependencies:**
```bash
cd orchestrator
pip install -r requirements_api.txt
```

2. **Install pillar-specific dependencies:**
```bash
# Toxicity pillar
cd ../Toxicity/Toxicity
pip install -r requirements_toxicity.txt

# FCAM pillar
cd ../../FCAM_fixed/FCAM_fixed/Factual_Consistency_Accountability_Module
pip install -r requirements.txt

# Governance pillar
cd ../../../Governance_Project/Governance_Project
pip install -r requirements.txt
```

### Running the API Server

```bash
cd orchestrator
python api_server.py
```

The server will start on `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs

### Running the Frontend

Open `frontend/site/web/index.html` in a web browser, or serve it with a simple HTTP server:

```bash
cd frontend/site/web
python -m http.server 3000
```

Then visit: http://localhost:3000

## 📚 API Usage

### Python Client Example

```python
from test_client import MyelinClient

# Initialize client
client = MyelinClient("http://localhost:8000")

# Comprehensive conversation audit
result = client.audit_conversation(
    user_input="Tell me about climate change",
    bot_response="Climate change is a serious issue...",
    source_text="Climate change refers to long-term shifts..."
)

print(f"Decision: {result['overall']['decision']}")
print(f"Risk Level: {result['overall']['risk_level']}")
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello, how are you?",
    "bot_response": "I am doing well, thank you!",
    "source_text": null
  }'
```

### JavaScript/Fetch Example

```javascript
const response = await fetch('http://localhost:8000/api/v1/audit/conversation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_input: "Your question",
        bot_response: "AI response",
        source_text: "Reference text"
    })
});

const result = await response.json();
console.log(result.overall.decision);
```

## 🔌 API Endpoints

### Comprehensive Audit
- **POST** `/api/v1/audit/conversation` - Run all applicable pillars on a conversation

### Individual Pillars
- **POST** `/api/v1/audit/fairness` - ML model fairness audit
- **POST** `/api/v1/audit/factual` - Factual consistency check
- **POST** `/api/v1/audit/toxicity` - Toxicity detection
- **POST** `/api/v1/audit/governance` - Governance compliance check

### Batch Operations
- **POST** `/api/v1/audit/batch/conversations` - Batch conversation audits

### Utility
- **GET** `/` - API information
- **GET** `/health` - Health check
- **GET** `/docs` - Interactive API documentation
- **GET** `/redoc` - Alternative API documentation

## 📊 Response Format

### Conversation Audit Response

```json
{
  "audit_type": "conversation",
  "timestamp": "2026-01-10T13:06:53.123456",
  "input": {
    "user": "User message",
    "bot": "Bot response",
    "source": "Reference text"
  },
  "pillars": {
    "toxicity": {
      "status": "success",
      "report": {
        "toxicity_score": 0.15,
        "risk_level": "LOW",
        "decision": "ALLOW"
      }
    },
    "governance": { ... },
    "factual": { ... }
  },
  "overall": {
    "risk_score": 0.234,
    "risk_level": "LOW",
    "decision": "ALLOW",
    "risk_factors": []
  }
}
```

## 🎨 Frontend Demo

The enhanced frontend includes:

- **Live API Demo** - Interactive testing of all pillars
- **Real-time Results** - Visual feedback with color-coded risk levels
- **Code Examples** - Integration snippets for developers
- **Responsive Design** - Works on desktop and mobile

### Demo Features

1. **Conversation Audit** - Test comprehensive AI governance
2. **Toxicity Check** - Detect harmful content
3. **Factual Verification** - Check accuracy and hallucinations
4. **Fairness Analysis** - Analyze ML model bias

## 🧪 Testing

### Test the Orchestrator Directly

```bash
cd orchestrator
python myelin_orchestrator.py
```

### Test via API Client

```bash
cd orchestrator
python test_client.py
```

### Test Individual Pillars

```bash
# Fairness
cd Myelin_Fairness_Pillar_RICH_FINAL
python main.py

# Factual Check
cd FCAM_fixed/FCAM_fixed/Factual_Consistency_Accountability_Module
python main.py

# Toxicity
cd Toxicity/Toxicity
python main.py

# Governance
cd Governance_Project/Governance_Project
python main.py
```

## 🔧 Configuration

### API Server Configuration

Edit `orchestrator/api_server.py`:

```python
# Change port
uvicorn.run("api_server:app", port=8000)

# Enable/disable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
)
```

### Frontend API URL

Edit `frontend/demo.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## 📈 Performance

- **Latency:** ~500ms - 2s per comprehensive audit (depends on pillar complexity)
- **Throughput:** Supports concurrent requests via FastAPI async
- **Scalability:** Can be deployed with multiple workers using Gunicorn/Uvicorn

## 🚢 Deployment

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install -r orchestrator/requirements_api.txt
RUN pip install -r Toxicity/Toxicity/requirements_toxicity.txt
# ... install other pillar dependencies

EXPOSE 8000

CMD ["python", "orchestrator/api_server.py"]
```

### Production Deployment

```bash
# Using Gunicorn with Uvicorn workers
gunicorn orchestrator.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 🛡️ Security Considerations

1. **API Authentication:** Add API key validation for production
2. **Rate Limiting:** Implement rate limiting to prevent abuse
3. **Input Validation:** All inputs are validated via Pydantic models
4. **CORS:** Configure allowed origins in production
5. **HTTPS:** Use HTTPS in production environments

## 📝 License

[Your License Here]

## 👥 Contributors

[Your Team Information]

## 📧 Support

For issues and questions:
- GitHub Issues: [Your Repo]
- Email: [Your Email]
- Documentation: http://localhost:8000/docs

## 🎯 Roadmap

- [ ] Add authentication and API key management
- [ ] Implement caching for improved performance
- [ ] Add support for custom rules via API
- [ ] Create SDKs for popular languages (JavaScript, Java, Go)
- [ ] Add monitoring and analytics dashboard
- [ ] Support for streaming/real-time audits
- [ ] Integration with popular AI platforms (OpenAI, Anthropic, etc.)

## 🙏 Acknowledgments

Built with:
- FastAPI
- Pydantic
- Uvicorn
- And the amazing open-source community

---

**MYELIN** - Making AI Safer, Fairer, and More Accountable 🛡️
