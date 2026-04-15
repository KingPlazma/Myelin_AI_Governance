import logging
import os
import re
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
        prompt_summary = self._build_myelin_summary(prompt_audit, request_id=request_id)
        prompt_summary["stage"] = "prompt"

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
                "myelin": prompt_summary,
                "myelin_prompt": prompt_summary
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

        response_summary = self._build_myelin_summary(response_audit, request_id=request_id)
        response_summary["remediated"] = remediated_reply != bot_reply

        llm_result["myelin"] = response_summary
        llm_result["myelin_prompt"] = prompt_summary

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

    async def handle_text_audit(
        self,
        text: str,
        raw_headers: Dict[str, str],
        route: str = "/v1/audit/text"
    ) -> Dict[str, Any]:
        self.metrics.record_request()
        request_id = str(uuid4())
        user_prompt = text or ""
        alert_email = await resolve_alert_email(
            raw_headers=raw_headers,
            allow_fallback_email=self.settings.allow_fallback_email,
            alert_email_header=self.settings.alert_email_header,
            alert_email=self.settings.alert_email
        )

        # In text-only mode, treat selected text as response content for policy checks.
        # Some pillars score output behavior more strongly than user-input framing.
        prompt_audit = self.agent_core.audit_conversation(
            user_input="",
            bot_response=user_prompt,
            source_text=user_prompt
        )
        prompt_summary = self._build_myelin_summary(prompt_audit, request_id=request_id)
        self._augment_structural_bias_signals(prompt_summary, user_prompt)
        prompt_summary["stage"] = "response_text"

        if prompt_summary.get("decision") == "BLOCK" and self.settings.strict_mode:
            self.metrics.record_block()

        schedule_flag_email(alert_email, prompt_audit, "agent_prompt")

        incident = self._build_incident(
            request_id=request_id,
            route=route,
            model="text-audit",
            user_prompt=user_prompt,
            bot_response=None,
            remediated_response=None,
            audit_report=prompt_audit,
            alert_email=alert_email
        )
        self.incident_store.append(incident)

        return {
            "mode": "text_audit",
            "myelin": prompt_summary,
            "myelin_prompt": prompt_summary,
            "audit_report": prompt_audit
        }

    def recent_incidents(self, limit: int = 20):
        return [record.model_dump() for record in self.incident_store.recent(limit=limit)]

    def current_metrics(self) -> Dict[str, int]:
        return self.metrics.snapshot()

    @staticmethod
    def _build_myelin_summary(audit_report: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        overall = audit_report.get("overall", {})

        # Collect per-pillar violations for UI display.
        triggered_pillars = []
        for pillar_name, pillar_data in audit_report.get("pillars", {}).items():
            report = pillar_data.get("report", {})
            violations = MyelinAgentService._extract_violations(report)
            if violations:
                triggered_pillars.append({
                    "pillar": pillar_name,
                    "violations": violations
                })

        return {
            "request_id": request_id,
            "decision": overall.get("decision", "ALLOW"),
            "risk_level": overall.get("risk_level", "LOW"),
            "risk_score": overall.get("risk_score", 0.0),
            "risk_factors": overall.get("risk_factors", []),
            "triggered_pillars": triggered_pillars,
        }

    @staticmethod
    def _extract_violations(report: Dict[str, Any]) -> list[Dict[str, Any]]:
        extracted: list[Dict[str, Any]] = []

        explicit = report.get("violations")
        if isinstance(explicit, list):
            for item in explicit:
                if not isinstance(item, dict):
                    continue
                extracted.append({
                    "rule": item.get("rule_name") or item.get("rule_id") or item.get("name", "Unknown Rule"),
                    "reason": item.get("reason", ""),
                    "severity": item.get("severity", ""),
                })

        details = report.get("details")
        if isinstance(details, list):
            for item in details:
                if not isinstance(item, dict) or not item.get("violation"):
                    continue

                entry = {
                    "rule": item.get("rule_name") or item.get("rule_id") or item.get("name", "Unknown Rule"),
                    "reason": item.get("reason", ""),
                    "severity": item.get("severity", ""),
                }

                if not any(
                    existing.get("rule") == entry.get("rule") and existing.get("reason") == entry.get("reason")
                    for existing in extracted
                ):
                    extracted.append(entry)

        return extracted

    @staticmethod
    def _augment_structural_bias_signals(summary: Dict[str, Any], text: str) -> None:
        lowered = (text or "").lower()

        # Catch common hiring fairness risk phrasing that may not be covered by
        # the conversational bias ruleset.
        patterns = [
            r"hiring algorithm",
            r"ranks? candidates?",
            r"certain universities?",
            r"similar qualifications?",
            r"disparate impact",
            r"biased hiring",
            r"selection bias",
        ]

        matches = sum(1 for p in patterns if re.search(p, lowered))
        if matches < 2:
            return

        fairness_entry = {
            "pillar": "fairness",
            "violations": [
                {
                    "rule": "Structural Hiring Bias Signal",
                    "reason": "Detected language indicating potential institutional preference in ranking decisions.",
                    "severity": "medium",
                }
            ]
        }

        triggered = summary.setdefault("triggered_pillars", [])
        if not any(item.get("pillar") == "fairness" for item in triggered if isinstance(item, dict)):
            triggered.append(fairness_entry)

        risk_factors = summary.setdefault("risk_factors", [])
        factor_msg = "Potential structural hiring bias signal detected in selected text"
        if factor_msg not in risk_factors:
            risk_factors.append(factor_msg)

        current_score = float(summary.get("risk_score", 0.0) or 0.0)
        summary["risk_score"] = max(current_score, 0.45)

        if summary.get("decision") == "ALLOW":
            summary["decision"] = "WARN"
        if summary.get("risk_level") in {None, "LOW", "UNKNOWN"}:
            summary["risk_level"] = "MEDIUM"

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
