import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        if settings.environment == "development":
            return
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)
