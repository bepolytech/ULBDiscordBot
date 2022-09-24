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
    email_contact: str = "boscar.vs@gmail.com"

    def __init__(self):
        self.context: ssl.SSLContext = ssl.create_default_context()

    def content(self, target_email: str, token: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Discord - ULB email addresse vérification"
        msg["From"] = self.email_addr
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
        <br> Si vous recevez régulièrement ce type de mail par erreur, veuillez nous <a href="mailto: {self.email_contact}">contacter</a>.
    </p>
  </body>
</html>
"""

        msg.attach(MIMEText(html, "html"))

        return msg.as_string()

    def sendToken(self, target_email: str, token: str):
        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=self.context) as server:
            server.login(self.email_addr, self.auth_token)
            content: str = self.content(target_email, token)
            server.sendmail(self.email_addr, target_email, content)
