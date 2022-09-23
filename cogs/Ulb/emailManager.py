# -*- coding: utf-8 -*-
import os
import smtplib
import ssl


class EmailManager:

    email_addr: str = os.getenv("EMAIL_ADDR")
    port = 465  # For SSL
    auth_token: str = os.getenv("EMAIL_AUTH_TOKEN")

    def __init__(self):
        self.context: ssl.SSLContext = ssl.create_default_context()

    def sendToken(self, email: str, token: str):
        with smtplib.SMTP_SSL("smtp.gmail.com", self.port, context=self.context) as server:
            server.login(self.email_addr, self.auth_token)
            message = f"""\
Subject: ULB email verification for ULB discord servers

Token: {token}

"""
            server.sendmail(self.email_addr, email, message)
