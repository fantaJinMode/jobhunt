"""Send the digest over SMTP. Gmail: use an App Password, not your login."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send(subject: str, html_body: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    # Gmail app passwords copy-paste with non-breaking spaces between the
    # 4-char groups; smtplib's AUTH PLAIN does a hard .encode('ascii') on
    # user+password, so a stray \xa0 crashes login with a cryptic
    # UnicodeEncodeError. Strip all whitespace, not just regular spaces.
    user = "".join(os.environ["SMTP_USER"].split())
    password = "".join(os.environ["SMTP_PASS"].split())
    to_addr = os.getenv("MAIL_TO", user)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content("This digest is HTML. Open it in an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls()
        s.login(user, password)
        s.send_message(msg)
    print(f"  mailed -> {to_addr}")
