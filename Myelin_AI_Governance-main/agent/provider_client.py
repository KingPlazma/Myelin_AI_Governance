from typing import Any, Dict

import httpx

from config import AgentSettings


class DownstreamLLMError(Exception):
    def __init__(self, status_code: int, detail: Any):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


class ProviderClient:
    def __init__(self, settings: AgentSettings):
        self.settings = settings

    def _headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        outgoing = dict(headers)
        if self.settings.provider_api_key and "authorization" not in outgoing:
            outgoing["authorization"] = f"Bearer {self.settings.provider_api_key}"
        return outgoing

    def _build_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        provider = self.settings.provider_type
        if provider in {"openai_compatible", "ollama"}:
            return payload
        if provider == "anthropic":
            messages = []
            system_parts = []
            for message in payload.get("messages", []):
                role = message.get("role", "user")
                content = message.get("content", "")
                if role == "system":
                    system_parts.append(content)
                    continue
                if role == "assistant":
                    messages.append({"role": "assistant", "content": content})
                else:
                    messages.append({"role": "user", "content": content})
            anthropic_payload = {
                "model": payload.get("model"),
                "messages": messages,
                "max_tokens": payload.get("max_tokens") or 512,
                "temperature": payload.get("temperature", 0.7)
            }
            if system_parts:
                anthropic_payload["system"] = "\n".join(system_parts)
            return anthropic_payload
        return payload

    def _normalize_response(self, response_payload: Dict[str, Any], model: str) -> Dict[str, Any]:
        provider = self.settings.provider_type
        if provider in {"openai_compatible", "ollama"}:
            return response_payload
        if provider == "anthropic":
            text_parts = []
            for block in response_payload.get("content", []):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            return {
                "id": response_payload.get("id", ""),
                "object": "chat.completion",
                "created": response_payload.get("created_at", ""),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "".join(text_parts).strip()
                    },
                    "finish_reason": response_payload.get("stop_reason", "stop")
                }]
            }
        return response_payload

    async def healthcheck(self) -> bool:
        async with httpx.AsyncClient(timeout=min(self.settings.request_timeout_seconds, 10.0)) as client:
            try:
                response = await client.get(
                    self.settings.target_llm_health_url,
                    headers=self._headers({})
                )
                return response.status_code < 500
            except Exception:
                return False

    async def chat_completion(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        outgoing_payload = self._build_payload(payload)
        outgoing_headers = self._headers(headers)
        if self.settings.provider_type == "anthropic":
            outgoing_headers.setdefault("x-api-key", self.settings.provider_api_key)
            outgoing_headers.setdefault("anthropic-version", "2023-06-01")

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            try:
                response = await client.post(
                    self.settings.target_llm_url,
                    json=outgoing_payload,
                    headers=outgoing_headers
                )
            except httpx.HTTPError as exc:
                raise DownstreamLLMError(502, f"Target LLM unreachable: {exc}") from exc

        if response.status_code != 200:
            try:
                detail = response.json()
            except Exception:
                detail = response.text or "Error from downstream LLM"
            raise DownstreamLLMError(response.status_code, detail)

        try:
            response_payload = response.json()
        except Exception as exc:
            raise DownstreamLLMError(502, f"Invalid downstream JSON response: {exc}") from exc

        return self._normalize_response(response_payload, payload.get("model", ""))
