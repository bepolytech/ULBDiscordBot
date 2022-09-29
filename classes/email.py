# -*- coding: utf-8 -*-
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailManagerInstantiationError:
    """The excepetion to be call when EmailManager is instantiated"""

    def __init__(self) -> None:
        super().__init__("EmailManager should be used as a class, not as object.")


class EmailManager:
    """Represent the email manager.

    This should be used as a class, and not instantiated.

    Classmethods
    -----------
    send_token(targer_email: `str`, token: `str`)
        Send an email for the token verification
    """

    _email_addr: str = os.getenv("EMAIL_ADDR")
    _port = 465  # For SSL
    _auth_token: str = os.getenv("EMAIL_AUTH_TOKEN")
    _context: ssl.SSLContext = ssl.create_default_context()

    @classmethod
    def _content(cls, target_email: str, token: str):
        """Create email content.

        Parameters
        ----------
        target_email: `str`
            The email address of the receiver
        token: `str`
            The token to inlude in the email
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Discord - ULB email adresse vérification"
        msg["From"] = cls._email_addr
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
        <br> Si vous recevez régulièrement ce type de mail par erreur, veuillez nous <a href="mailto: {cls._email_addr}">contacter</a>.
    </p>
  </body>
</html>
"""

        msg.attach(MIMEText(html, "html"))

        return msg.as_string()

    @classmethod
    def send_token(cls, target_email: str, token: str):
        """Send an email with the token verification

        Parameters
        ----------
        target_email : `str`
            The address email of the receiver
        token : `str`
            The token to include in the email
        """
        with smtplib.SMTP_SSL("smtp.gmail.com", cls._port, context=cls._context) as server:
            server.login(cls._email_addr, cls._auth_token)
            content: str = cls._content(target_email, token)
            server.sendmail(cls._email_addr, target_email, content)
            logging.trace(f"[EMAIL] Token email sent to {target_email}")
