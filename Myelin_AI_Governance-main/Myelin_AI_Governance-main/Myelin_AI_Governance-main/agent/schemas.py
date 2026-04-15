from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    strict_mode: bool
    downstream_reachable: bool


class IncidentRecord(BaseModel):
    request_id: str
    timestamp: str
    route: str
    model: str
    decision: str
    risk_level: str
    risk_score: float
    user_prompt: str
    bot_response: Optional[str] = None
    remediated_response: Optional[str] = None
    audit_report: Dict[str, Any]
    alert_email: Optional[str] = None
