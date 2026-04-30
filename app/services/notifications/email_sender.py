import logging
import smtplib
import ssl
import time
from email.mime.text import MIMEText

from app.config.settings import settings

logger = logging.getLogger(__name__)


def send_results_email(body: str) -> None:
    """
    Sends final ranked posts via Gmail SMTP using TLS and app-password auth.
    """
    if not settings.EMAIL_USER or not settings.EMAIL_PASS or not settings.EMAIL_RECEIVER:
        raise ValueError("Email settings are incomplete. Check EMAIL_USER, EMAIL_PASS, and EMAIL_RECEIVER.")

    # Split comma-separated emails if present
    receivers = [email.strip() for email in settings.EMAIL_RECEIVER.split(",") if email.strip()]
    if not receivers:
        raise ValueError("No valid email receivers found in EMAIL_RECEIVER.")

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = "Reddit AI Agent: Today's High-Importance Digest"
    message["From"] = settings.EMAIL_USER
    message["To"] = ", ".join(receivers)

    ssl_context = ssl.create_default_context()
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30, context=ssl_context) as server:
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.sendmail(settings.EMAIL_USER, receivers, message.as_string())
            logger.info("Email sent successfully to %s.", ", ".join(receivers))
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