import os
import smtplib
from email.mime.text import MIMEText
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery("proxy", broker=REDIS_URL, backend=REDIS_URL)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@proxy.com")


@celery.task
def send_activation_email(email, key):
    print(f"[celery] sending email to {email}")

    if not SMTP_USER:
        # smtp не настроен, просто выводим в консоль
        print(f"[EMAIL] to={email} | key={key}")
        return

    msg = MIMEText(f"Привет!\n\nТвой ключ активации: {key}\n\nВставь его в десктопное приложение.")
    msg["Subject"] = "Ключ активации прокси"
    msg["From"] = EMAIL_FROM
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(EMAIL_FROM, email, msg.as_string())
        print(f"[celery] email sent ok")
    except Exception as e:
        print(f"[celery] email error: {e}")
