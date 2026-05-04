import logging
import smtplib
import ssl
import time
from email.mime.text import MIMEText
import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _send_via_sendgrid(subject: str, body: str, to_emails: list[str]) -> None:
    """Send email via SendGrid Web API synchronously using httpx."""
    if not settings.SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY is not configured")

    from_email = settings.SENDGRID_FROM or settings.EMAIL_USER
    if not from_email:
        raise ValueError("No from address configured for SendGrid (SENDGRID_FROM or EMAIL_USER)")

    payload = {
        "personalizations": [{"to": [{"email": e} for e in to_emails]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }

    headers = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}", "Content-Type": "application/json"}

    # Use a short timeout and raise for status to bubble up errors
    with httpx.Client(timeout=15.0) as client:
        resp = client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
        resp.raise_for_status()


def send_results_email(body: str) -> None:
    """
    Sends final ranked posts via SendGrid (preferred) or Gmail SMTP (fallback).
    """
    # Prepare recipients
    if not settings.EMAIL_RECEIVER:
        raise ValueError("No EMAIL_RECEIVER configured")

    receivers = [email.strip() for email in settings.EMAIL_RECEIVER.split(",") if email.strip()]
    if not receivers:
        raise ValueError("No valid email receivers found in EMAIL_RECEIVER.")

    subject = "Reddit AI Agent: Today's High-Importance Digest"

    # If SendGrid is configured, use it first
    if settings.SENDGRID_API_KEY:
        try:
            _send_via_sendgrid(subject, body, receivers)
            logger.info("Email sent successfully via SendGrid to %s.", ", ".join(receivers))
            return
        except Exception as e:
            logger.warning("SendGrid send failed: %s; falling back to SMTP", e)

    # Fallback to SMTP
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        raise ValueError("Email settings are incomplete for SMTP fallback. Check EMAIL_USER and EMAIL_PASS.")

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_USER
    message["To"] = ", ".join(receivers)

    ssl_context = ssl.create_default_context()
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls(context=ssl_context)
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.sendmail(settings.EMAIL_USER, receivers, message.as_string())
            logger.info("Email sent successfully via SMTP to %s.", ", ".join(receivers))
            return
        except (smtplib.SMTPException, OSError, TimeoutError) as error:
            last_error = error
            logger.warning(
                "Email send attempt %s failed: %s: %s",
                attempt + 1,
                type(error).__name__,
                error,
            )
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to send email after retries: {last_error}") from last_error