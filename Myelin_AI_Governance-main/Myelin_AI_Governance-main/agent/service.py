import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from alerting import resolve_alert_email, schedule_flag_email
from config import AgentSettings
from incident_store import IncidentStore
from metrics import MetricsCollector
from provider_client import DownstreamLLMError, ProviderClient
from schemas import ChatCompletionRequest, IncidentRecord


base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_path not in sys.path:
    sys.path.append(base_path)

from agent_core import get_agent_core


logger = logging.getLogger("MyelinAgentService")


class MyelinAgentService:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.provider = ProviderClient(settings)
        self.incident_store = IncidentStore(settings.incident_db_path)
        self.metrics = MetricsCollector()
        self.agent_core = get_agent_core()

    async def readiness(self) -> bool:
        return await self.provider.healthcheck()

    async def handle_chat_completion(
        self,
        request: ChatCompletionRequest,
        raw_headers: Dict[str, str],
        route: str = "/v1/chat/completions"
    ) -> Dict[str, Any]:
        if request.stream:
            raise DownstreamLLMError(501, "Streaming is not enabled in this Myelin service build.")

        self.metrics.record_request()
        request_id = str(uuid4())
        user_prompt = request.messages[-1].content if request.messages else ""
        alert_email = await resolve_alert_email(
            raw_headers=raw_headers,
            allow_fallback_email=self.settings.allow_fallback_email,
            alert_email_header=self.settings.alert_email_header,
            alert_email=self.settings.alert_email
        )

        prompt_audit = self.agent_core.audit_conversation(user_prompt, bot_response="")
        prompt_overall = prompt_audit.get("overall", {})

        if prompt_overall.get("decision") == "BLOCK" and self.settings.strict_mode:
            self.metrics.record_block()
            schedule_flag_email(alert_email, prompt_audit, "agent_prompt")
            incident = self._build_incident(
                request_id=request_id,
                route=route,
                model=request.model,
                user_prompt=user_prompt,
                bot_response=None,
                remediated_response=None,
                audit_report=prompt_audit,
                alert_email=alert_email
            )
            self.incident_store.append(incident)
            return {
                "id": f"myelin-blocked-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I apologize, but your request violates governance policies and has been blocked by the Myelin Sentinel Agent."
                    },
                    "finish_reason": "content_filter"
                }],
                "myelin": {
                    "request_id": request_id,
                    "decision": prompt_overall.get("decision", "BLOCK"),
                    "risk_level": prompt_overall.get("risk_level", "HIGH"),
                    "risk_score": prompt_overall.get("risk_score", 1.0),
                    "stage": "prompt"
                }
            }

        payload = request.model_dump()
        # Only forward explicit auth-related headers downstream.
        # Browser-origin headers such as Origin/Sec-Fetch-* can cause local providers
        # like Ollama to reject requests with 403 even though the same payload is valid.
        allowed_forward_headers = {"authorization", "x-api-key"}
        forward_headers = {
            key: value
            for key, value in raw_headers.items()
            if key.lower() in allowed_forward_headers
        }
        try:
            llm_result = await self.provider.chat_completion(payload=payload, headers=forward_headers)
        except DownstreamLLMError:
            self.metrics.record_downstream_error()
            raise
        bot_reply = llm_result["choices"][0]["message"]["content"]

        response_audit = self.agent_core.audit_conversation(user_prompt, bot_response=bot_reply)
        schedule_flag_email(alert_email, response_audit, "agent_response")
        remediated_reply = self.agent_core.remediate(bot_reply, response_audit)

        if remediated_reply != bot_reply:
            self.metrics.record_remediation()
            llm_result["choices"][0]["message"]["content"] = remediated_reply

        overall = response_audit.get("overall", {})
        llm_result["myelin"] = {
            "request_id": request_id,
            "decision": overall.get("decision", "ALLOW"),
            "risk_level": overall.get("risk_level", "LOW"),
            "risk_score": overall.get("risk_score", 0.0),
            "remediated": remediated_reply != bot_reply
        }

        incident = self._build_incident(
            request_id=request_id,
            route=route,
            model=request.model,
            user_prompt=user_prompt,
            bot_response=bot_reply,
            remediated_response=remediated_reply if remediated_reply != bot_reply else None,
            audit_report=response_audit,
            alert_email=alert_email
        )
        self.incident_store.append(incident)
        return llm_result

    def recent_incidents(self, limit: int = 20):
        return [record.model_dump() for record in self.incident_store.recent(limit=limit)]

    def current_metrics(self) -> Dict[str, int]:
        return self.metrics.snapshot()

    def _build_incident(
        self,
        request_id: str,
        route: str,
        model: str,
        user_prompt: str,
        bot_response: Optional[str],
        remediated_response: Optional[str],
        audit_report: Dict[str, Any],
        alert_email: Optional[str]
    ) -> IncidentRecord:
        overall = audit_report.get("overall", {})
        stored_prompt = "[REDACTED]" if self.settings.redact_request_bodies_in_logs else user_prompt

        return IncidentRecord(
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            route=route,
            model=model,
            decision=overall.get("decision", "UNKNOWN"),
            risk_level=overall.get("risk_level", "UNKNOWN"),
            risk_score=float(overall.get("risk_score", 0.0) or 0.0),
            user_prompt=stored_prompt,
            bot_response=bot_response,
            remediated_response=remediated_response,
            audit_report=audit_report,
            alert_email=alert_email
        )
