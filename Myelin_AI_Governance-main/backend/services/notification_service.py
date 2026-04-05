"""
Notification Service
Handles email verification and conditional audit alert delivery with PDF attachments.
"""

import json
import logging
import os
import smtplib
import tempfile
from datetime import datetime
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for transactional email notifications."""

    @staticmethod
    def is_enabled() -> bool:
        """Return True when email sending is fully configured."""
        return all([
            settings.EMAIL_ENABLED,
            settings.EMAIL_SMTP_HOST,
            settings.EMAIL_SMTP_USERNAME,
            settings.EMAIL_SMTP_PASSWORD,
            settings.EMAIL_FROM,
        ])

    @staticmethod
    def has_flags(report_data: Dict[str, Any]) -> bool:
        """Determine if the audit report contains any flagged issues."""
        if not isinstance(report_data, dict):
            return False

        violations = NotificationService._collect_violations(report_data)
        if violations:
            return True

        overall = report_data.get("overall", {})
        if isinstance(overall, dict):
            decision = str(overall.get("decision", "")).upper()
            risk_level = str(overall.get("risk_level", "")).upper()
            if decision and decision != "ALLOW":
                return True
            if risk_level and risk_level not in {"LOW", "NONE"}:
                return True

        return False

    @staticmethod
    def send_verification_email(to_email: str, full_name: str, verification_url: str):
        """Send account verification email."""
        if not NotificationService.is_enabled():
            logger.info("Email disabled or not fully configured; skipping verification email")
            return

        subject = "Verify your MYELIN account"
        greeting_name = full_name or "there"
        text_body = (
            f"Hi {greeting_name},\n\n"
            "Thanks for signing up for MYELIN. Please verify your email address by opening the link below:\n\n"
            f"{verification_url}\n\n"
            "This link expires soon. If you did not sign up, you can safely ignore this email.\n"
        )
        html_body = _build_verification_html(greeting_name, verification_url)

        NotificationService._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            attachments=[]
        )

    @staticmethod
    def send_audit_report_if_flagged(to_email: str, audit_type: str, report_data: Dict[str, Any]):
        """Send audit report email only when violations or elevated risk are present."""
        if not NotificationService.has_flags(report_data):
            logger.info("No flags in audit report; email skipped")
            return

        if not NotificationService.is_enabled():
            logger.info("Email disabled or not fully configured; skipping flagged report email")
            return

        pdf_path = None
        try:
            pdf_path = NotificationService._build_pdf_from_report(report_data, audit_type)
            subject = f"MYELIN Alert: Flags detected in {audit_type} audit"
            text_body = (
                "Your recent audit execution detected one or more flags.\n\n"
                "Attached is a PDF version of the generated JSON report so you can review the details.\n"
            )
            html_body = _build_alert_html(audit_type)
            NotificationService._send_email(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                attachments=[pdf_path]
            )
            logger.info(f"Flagged audit email sent to {to_email} for {audit_type}")
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)

    @staticmethod
    def _send_email(to_email: str, subject: str, text_body: str, attachments: List[str],
                    html_body: Optional[str] = None):
        """Build and send an email with optional attachments."""
        message = EmailMessage()
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(text_body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        for file_path in attachments:
            with open(file_path, "rb") as file_stream:
                file_bytes = file_stream.read()
            filename = os.path.basename(file_path)
            message.add_attachment(
                file_bytes,
                maintype="application",
                subtype="pdf",
                filename=filename,
            )

        if settings.EMAIL_USE_TLS:
            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(settings.EMAIL_SMTP_USERNAME, settings.EMAIL_SMTP_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as smtp:
                smtp.login(settings.EMAIL_SMTP_USERNAME, settings.EMAIL_SMTP_PASSWORD)
                smtp.send_message(message)

    @staticmethod
    def _collect_violations(report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect violation dictionaries from known report structures."""
        found: List[Dict[str, Any]] = []

        # Flat report format
        report = report_data.get("report", {})
        if isinstance(report, dict):
            for violation in report.get("violations", []):
                if isinstance(violation, dict):
                    found.append(violation)

        # Pillar-based format
        pillars = report_data.get("pillars", {})
        if isinstance(pillars, dict):
            for pillar_data in pillars.values():
                if not isinstance(pillar_data, dict):
                    continue
                pillar_report = pillar_data.get("report", {})
                if not isinstance(pillar_report, dict):
                    continue
                for violation in pillar_report.get("violations", []):
                    if isinstance(violation, dict):
                        found.append(violation)

        return found

    @staticmethod
    def _build_verification_html(full_name: str, verification_url: str) -> str:
        """Build HTML content for account verification emails."""
        return f"""
<html>
    <body style=\"font-family:Segoe UI, Arial, sans-serif; color:#1f2937; line-height:1.6;\">
        <h2 style=\"margin-bottom:8px;\">Verify your MYELIN account</h2>
        <p>Hi {full_name},</p>
        <p>Thanks for signing up for MYELIN. Please verify your email address to activate your account.</p>
        <p>
            <a href=\"{verification_url}\" style=\"display:inline-block; background:#0f766e; color:white; padding:10px 16px; text-decoration:none; border-radius:6px;\">Verify Email</a>
        </p>
        <p>If the button does not work, open this URL directly:</p>
        <p><a href=\"{verification_url}\">{verification_url}</a></p>
        <p style=\"font-size:12px; color:#6b7280;\">If you did not sign up, you can ignore this email.</p>
    </body>
</html>
""".strip()

    @staticmethod
    def _build_alert_html(audit_type: str) -> str:
        """Build HTML content for flagged audit alert emails."""
        safe_audit_type = str(audit_type).replace("<", "").replace(">", "")
        return f"""
<html>
    <body style=\"font-family:Segoe UI, Arial, sans-serif; color:#1f2937; line-height:1.6;\">
        <h2 style=\"margin-bottom:8px; color:#b91c1c;\">MYELIN Alert: Flags detected</h2>
        <p>The latest <strong>{safe_audit_type}</strong> audit raised one or more flags.</p>
        <p>Please review the attached PDF report for details, impacted rules, and risk indicators.</p>
    </body>
</html>
""".strip()

    @staticmethod
    def _build_pdf_from_report(report_data: Dict[str, Any], audit_type: str) -> str:
        """Render JSON report into a simple readable PDF file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audit_type}_report.pdf") as temp_file:
            pdf_path = temp_file.name

        lines = [
            f"MYELIN Audit Report ({audit_type})",
            f"Generated at: {datetime.utcnow().isoformat()}Z",
            "",
        ]
        for raw_line in json.dumps(report_data, indent=2, default=str).splitlines():
            if not raw_line:
                lines.append("")
                continue
            for i in range(0, len(raw_line), 100):
                lines.append(raw_line[i:i + 100])

        NotificationService._write_simple_pdf(pdf_path, lines)
        return pdf_path

    @staticmethod
    def _escape_pdf_text(text: str) -> str:
        """Escape text for safe PDF text objects."""
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    @staticmethod
    def _write_simple_pdf(path: str, lines: List[str]):
        """Write a basic multi-page text PDF without external dependencies."""
        max_lines_per_page = 55
        pages: List[List[str]] = []
        for idx in range(0, len(lines), max_lines_per_page):
            pages.append(lines[idx:idx + max_lines_per_page])
        if not pages:
            pages = [[""]]

        objects: List[bytes] = []

        # Object 1: catalog, Object 2: pages root, Object 3: font
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"__PAGES_PLACEHOLDER__")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

        page_object_ids: List[int] = []
        content_object_ids: List[int] = []

        for page_lines in pages:
            escaped_lines = [NotificationService._escape_pdf_text(line) for line in page_lines]
            text_commands = "\\n".join(f"({line}) Tj T*" for line in escaped_lines)
            stream_text = (
                "BT\\n"
                "/F1 9 Tf\\n"
                "50 790 Td\\n"
                "12 TL\\n"
                f"{text_commands}\\n"
                "ET"
            )
            stream_bytes = stream_text.encode("latin-1", errors="replace")
            content_object = (
                b"<< /Length " + str(len(stream_bytes)).encode("ascii") + b" >>\\n"
                b"stream\\n" + stream_bytes + b"\\nendstream"
            )
            objects.append(content_object)
            content_id = len(objects)
            content_object_ids.append(content_id)

            page_object = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
            objects.append(page_object)
            page_id = len(objects)
            page_object_ids.append(page_id)

        kids = " ".join(f"{obj_id} 0 R" for obj_id in page_object_ids)
        pages_root = f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_object_ids)} >>".encode("ascii")
        objects[1] = pages_root

        with open(path, "wb") as pdf_file:
            pdf_file.write(b"%PDF-1.4\\n")
            offsets = [0]

            for index, obj in enumerate(objects, start=1):
                offsets.append(pdf_file.tell())
                pdf_file.write(f"{index} 0 obj\\n".encode("ascii"))
                pdf_file.write(obj)
                pdf_file.write(b"\\nendobj\\n")

            xref_offset = pdf_file.tell()
            pdf_file.write(f"xref\\n0 {len(objects) + 1}\\n".encode("ascii"))
            pdf_file.write(b"0000000000 65535 f \\n")
            for offset in offsets[1:]:
                pdf_file.write(f"{offset:010d} 00000 n \\n".encode("ascii"))

            trailer = (
                f"trailer\\n<< /Size {len(objects) + 1} /Root 1 0 R >>\\n"
                f"startxref\\n{xref_offset}\\n%%EOF"
            )
            pdf_file.write(trailer.encode("ascii"))


notification_service = NotificationService()


def _build_verification_html(full_name: str, verification_url: str) -> str:
    """Build HTML content for account verification emails."""
    return f"""
<html>
    <body style=\"font-family:Segoe UI, Arial, sans-serif; color:#1f2937; line-height:1.6;\">
        <h2 style=\"margin-bottom:8px;\">Verify your MYELIN account</h2>
        <p>Hi {full_name},</p>
        <p>Thanks for signing up for MYELIN. Please verify your email address to activate your account.</p>
        <p>
            <a href=\"{verification_url}\" style=\"display:inline-block; background:#0f766e; color:white; padding:10px 16px; text-decoration:none; border-radius:6px;\">Verify Email</a>
        </p>
        <p>If the button does not work, open this URL directly:</p>
        <p><a href=\"{verification_url}\">{verification_url}</a></p>
        <p style=\"font-size:12px; color:#6b7280;\">If you did not sign up, you can ignore this email.</p>
    </body>
</html>
""".strip()


def _build_alert_html(audit_type: str) -> str:
    """Build HTML content for flagged audit alert emails."""
    safe_audit_type = str(audit_type).replace("<", "").replace(">", "")
    return f"""
<html>
    <body style=\"font-family:Segoe UI, Arial, sans-serif; color:#1f2937; line-height:1.6;\">
        <h2 style=\"margin-bottom:8px; color:#b91c1c;\">MYELIN Alert: Flags detected</h2>
        <p>The latest <strong>{safe_audit_type}</strong> audit raised one or more flags.</p>
        <p>Please review the attached PDF report for details, impacted rules, and risk indicators.</p>
    </body>
</html>
""".strip()


def get_notification_service() -> NotificationService:
    """Get notification service singleton."""
    return notification_service
