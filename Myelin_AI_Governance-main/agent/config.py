import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _default_health_url(target_url: str) -> str:
    if "/v1/chat/completions" in target_url:
        return target_url.replace("/v1/chat/completions", "/v1/models")
    return target_url


@dataclass(frozen=True)
class AgentSettings:
    service_name: str
    service_version: str
    host: str
    port: int
    log_level: str
    strict_mode: bool
    request_timeout_seconds: float
    provider_type: str
    provider_api_key: str
    target_llm_url: str
    target_llm_health_url: str
    incident_db_path: str
    allow_fallback_email: bool
    alert_email: str
    alert_email_header: str
    redact_request_bodies_in_logs: bool
    operational_token: str


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    target_llm_url = os.getenv("TARGET_LLM_URL", "http://localhost:11434/v1/chat/completions")
    target_llm_health_url = os.getenv("TARGET_LLM_HEALTH_URL", _default_health_url(target_llm_url))
    incident_db_path = os.getenv(
        "MYELIN_INCIDENT_DB_PATH",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "incidents.sqlite3")
    )

    return AgentSettings(
        service_name=os.getenv("MYELIN_SERVICE_NAME", "Myelin Sentinel Agent Proxy"),
        service_version=os.getenv("MYELIN_SERVICE_VERSION", "1.1.0"),
        host=os.getenv("MYELIN_HOST", "0.0.0.0"),
        port=int(os.getenv("MYELIN_PORT", "9000")),
        log_level=os.getenv("MYELIN_LOG_LEVEL", "INFO").upper(),
        strict_mode=_env_bool("MYELIN_STRICT_MODE", True),
        request_timeout_seconds=_env_float("MYELIN_REQUEST_TIMEOUT_SECONDS", 120.0),
        provider_type=os.getenv("MYELIN_PROVIDER_TYPE", "openai_compatible").strip().lower(),
        provider_api_key=os.getenv("MYELIN_PROVIDER_API_KEY", "").strip(),
        target_llm_url=target_llm_url,
        target_llm_health_url=target_llm_health_url,
        incident_db_path=incident_db_path,
        allow_fallback_email=_env_bool("AGENT_ALLOW_FALLBACK_EMAIL", False),
        alert_email=os.getenv("AGENT_ALERT_EMAIL", ""),
        alert_email_header=os.getenv("AGENT_ALERT_EMAIL_HEADER", "X-User-Email"),
        redact_request_bodies_in_logs=_env_bool("MYELIN_REDACT_REQUEST_BODIES_IN_LOGS", False),
        operational_token=os.getenv("MYELIN_OPERATIONAL_TOKEN", "")
    )
