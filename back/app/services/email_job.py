from app.services.email import send_email


def send_email_job(to: str, subject: str, body: str) -> None:
    send_email(to, subject, body)
