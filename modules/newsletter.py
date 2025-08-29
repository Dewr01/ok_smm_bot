# modules/newsletter.py
import os
import smtplib
from email.mime.text import MIMEText

from . import ModuleBase


class NewsletterModule(ModuleBase):
    name = "newsletter"
    title = "Email/OK рассылки (email часть)"

    def send_email(self, to_addr: str, subject: str, body: str):
        host = os.getenv("SMTP_HOST", "")
        port = int(os.getenv("SMTP_PORT", "587"))
        user = os.getenv("SMTP_USER", "")
        pwd = os.getenv("SMTP_PASS", "")
        from_addr = os.getenv("SMTP_FROM", user)
        if not host or not user or not pwd: return False
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(from_addr, [to_addr], msg.as_string())
        return True
