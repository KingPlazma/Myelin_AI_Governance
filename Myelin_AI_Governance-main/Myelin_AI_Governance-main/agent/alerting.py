import asyncio
import logging
from typing import Any, Dict, Optional


logger = logging.getLogger("MyelinAlerting")


def extract_api_key_from_headers(headers: Dict[str, str]) -> Optional[str]:
    api_key = headers.get("x-api-key")
    if api_key:
        return api_key

    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "", 1)

    return None


async def resolve_alert_email(
    raw_headers: Dict[str, str],
    allow_fallback_email: bool,
    alert_email_header: str,
    alert_email: str
) -> Optional[str]:
    api_key = extract_api_key_from_headers(raw_headers)
    if api_key:
        try:
            from backend.services.auth_service import get_auth_service

            auth_context = await get_auth_service().validate_api_key(api_key)
            if auth_context and auth_context.get("user", {}).get("email"):
                return auth_context["user"]["email"]
        except Exception as exc:
            logger.warning("Could not resolve email from API key: %s", exc)

    if allow_fallback_email:
        header_email = raw_headers.get(alert_email_header.lower())
        if header_email:
            return header_email
        if alert_email:
            return alert_email

    return None


def schedule_flag_email(recipient_email: Optional[str], report_data: Dict[str, Any], audit_type: str) -> None:
    if not recipient_email:
        return

    try:
        from backend.services.notification_service import get_notification_service

        notification_service = get_notification_service()
        if not notification_service.has_flags(report_data):
            return

        asyncio.create_task(asyncio.to_thread(
            notification_service.send_audit_report_if_flagged,
            recipient_email,
            audit_type,
            report_data
        ))
    except Exception as exc:
        logger.warning("Failed to schedule agent alert email: %s", exc)
