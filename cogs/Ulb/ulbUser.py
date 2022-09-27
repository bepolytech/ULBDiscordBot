# -*- coding: utf-8 -*-


class UlbUser:
    def __init__(self, name: str, email: str):
        self.name: str = name
        self.email: str = email

    def __iter__(self):
        yield "name", self.name
        yield "email", self.email
