import os
import uvicorn
import httpx
import time
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime

from agent_core import get_agent_core

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MyelinProxyAgent")

app = FastAPI(
    title="Myelin Sentinel Agent Proxy",
    description="Drop-in 24/7 AI Governance Agent",
    version="1.0.0"
)

# Configuration (In production, move to env vars)
TARGET_LLM_URL = os.getenv("TARGET_LLM_URL", "http://localhost:11434/v1/chat/completions") # Default to Ollama
MYELIN_STRICT_MODE = os.getenv("MYELIN_STRICT_MODE", "true").lower() == "true"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Myelin Sentinel Agent...")
    # Trigger engine load
    get_agent_core()
    logger.info("Myelin Agent Engine Ready.")

@app.get("/health")
async def health():
    return {"status": "active", "agent": "Myelin Sentinel"}

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: ChatCompletionRequest, raw_request: Request):
    """
    OpenAI-compatible proxy that runs 24/7 governance.
    """
    user_prompt = request.messages[-1].content
    logger.info(f"Intercepted Prompt: {user_prompt[:50]}...")

    agent_core = get_agent_core()

    # 1. PRE-AUDIT (PROMPT DEFENSE)
    # Check if the user is asking for restricted things (e.g., prompt injection)
    prompt_audit = agent_core.audit_conversation(user_prompt, bot_response="")
    if prompt_audit["overall"]["decision"] == "BLOCK" and MYELIN_STRICT_MODE:
        logger.warning("🚩 BLOCKING MALICIOUS PROMPT")
        return {
            "id": "myelin-blocked-" + str(int(time.time())),
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "I apologize, but your request violates governance policies and has been blocked by the Myelin Sentinel Agent."},
                "finish_reason": "content_filter"
            }]
        }

    # 2. CALL REAL LLM
    logger.info(f"Forwarding to target LLM: {TARGET_LLM_URL}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Reconstruct payload to preserve any extra params
            payload = request.dict()
            headers = {k: v for k, v in raw_request.headers.items() if k.lower() not in ["host", "content-length"]}
            
            response = await client.post(TARGET_LLM_URL, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Error from target LLM: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error from downstream LLM")
            
            llm_result = response.json()
            bot_reply = llm_result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Failed to reach target LLM: {e}")
            raise HTTPException(status_code=502, detail="Target LLM unreachable")

    # 3. POST-AUDIT (RESPONSE DEFENSE & REMEDIATION)
    logger.info("Running Response Audit...")
    response_audit = agent_core.audit_conversation(user_prompt, bot_response=bot_reply)
    
    # 4. AGENTIC REMEDIATION
    remediated_reply = agent_core.remediate(bot_reply, response_audit)
    
    if remediated_reply != bot_reply:
        logger.info("✨ RESPONSE REMEDIATED BY AGENT")
        llm_result["choices"][0]["message"]["content"] = remediated_reply
        # Add Myelin headers for observability
        llm_result["myelin_audit"] = response_audit["overall"]

    # --- LOGGING FOR BACKGROUND OBSERVER ---
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_prompt": user_prompt,
        "bot_response": bot_reply,
        "remediated_response": remediated_reply if remediated_reply != bot_reply else None,
        "risk_score": response_audit.get("overall", {}).get("risk_score", 0)
    }
    try:
        with open("agent_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to log conversation for observer: {e}")

    return llm_result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
