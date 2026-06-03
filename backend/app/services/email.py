"""Email notifications. Toggle via EMAIL_PROVIDER (none|resend).

Failure-tolerant: a send error never breaks the claim flow.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _send_resend(to: str, subject: str, html: str) -> bool:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to)
        return False
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("Resend email to %s failed: %s", to, exc)
        return False


def send_email(to: str | None, subject: str, html: str) -> bool:
    """Send an email via the configured provider. Returns True if sent."""
    if not to or settings.email_provider == "none":
        return False
    if settings.email_provider == "resend":
        return _send_resend(to, subject, html)
    logger.warning("Unknown EMAIL_PROVIDER %r; email not sent", settings.email_provider)
    return False


def notify_claim_submitted(to: str | None, employee_name: str | None, claim_id) -> bool:
    link = f"{settings.frontend_url}/claims/{claim_id}"
    return send_email(
        to,
        "Your medical claim has been received",
        f"<p>Hi {employee_name or 'there'},</p>"
        f"<p>Your medical claim has been received and is being processed.</p>"
        f'<p><a href="{link}">View your claim</a></p>'
        f"<p>— {settings.app_name}</p>",
    )


def notify_claim_reviewed(
    to: str | None, employee_name: str | None, claim_id, decision: str, comment: str | None
) -> bool:
    link = f"{settings.frontend_url}/claims/{claim_id}"
    pretty = {"approve": "approved", "reject": "rejected", "needs_info": "returned for more info"}.get(
        decision, decision
    )
    note = f"<p>Reviewer note: {comment}</p>" if comment else ""
    return send_email(
        to,
        f"Your medical claim was {pretty}",
        f"<p>Hi {employee_name or 'there'},</p>"
        f"<p>Your medical claim has been <strong>{pretty}</strong>.</p>"
        f"{note}"
        f'<p><a href="{link}">View your claim</a></p>'
        f"<p>— {settings.app_name}</p>",
    )
