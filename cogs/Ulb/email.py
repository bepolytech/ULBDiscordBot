# -*- coding: utf-8 -*-
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailManager:

    email_addr: str = os.getenv("EMAIL_ADDR")
    port = 465  # For SSL
    auth_token: str = os.getenv("EMAIL_AUTH_TOKEN")
    context: ssl.SSLContext = ssl.create_default_context()

    @classmethod
    def content(cls, target_email: str, token: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Discord - ULB email adresse vérification"
        msg["From"] = cls.email_addr
        msg["To"] = target_email

        html = f"""\
<html>
  <head></head>
  <body>
    <p> Token de vérification : <code>{token}</code>
        <br>
        <br> Vous recevez ce message car vous avez demandé a lier votre compte discord avec votre addresse mail ULB affin d'accéder aux serveurs du BEP.
        <br>
        <br> Si vous n'êtes pas à l'origine de cette demande, ne tenez pas compte de ce mail.
        <br> Si vous recevez régulièrement ce type de mail par erreur, veuillez nous <a href="mailto: {cls.email_addr}">contacter</a>.
    </p>
  </body>
</html>
"""

        msg.attach(MIMEText(html, "html"))

        return msg.as_string()

    @classmethod
    def sendToken(cls, target_email: str, token: str):
        with smtplib.SMTP_SSL("smtp.gmail.com", cls.port, context=cls.context) as server:
            server.login(cls.email_addr, cls.auth_token)
            content: str = cls.content(target_email, token)
            server.sendmail(cls.email_addr, target_email, content)
