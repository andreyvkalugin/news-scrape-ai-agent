import os
import smtplib
from email.message import EmailMessage


class EmailClient:
    """
    Простой SMTP-клиент для отправки уведомлений.

    Конфигурация через переменные окружения:
      SMTP_HOST     — например, smtp.gmail.com
      SMTP_PORT     — например, 465 (SSL)
      SMTP_USER     — логин SMTP
      SMTP_PASSWORD — пароль или app-password
      SMTP_SENDER   — адрес "От" (по умолчанию равен SMTP_USER)
    """

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "465"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender = os.getenv("SMTP_SENDER", self.user)

    def send(self, subject: str, body: str, recipient: str) -> None:
        if not self.user or not self.password:
            raise RuntimeError(
                "SMTP_USER/SMTP_PASSWORD не заданы — отправка email невозможна."
            )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = recipient
        message.set_content(body)

        with smtplib.SMTP_SSL(self.host, self.port) as server:
            server.login(self.user, self.password)
            server.send_message(message)
