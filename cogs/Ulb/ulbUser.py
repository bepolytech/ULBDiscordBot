# -*- coding: utf-8 -*-


class UlbUser:
    """Represent an UlbUser

    Parameters
    ----------
    name: `str`
        The name of the user
    email: `str`
        The ulb email address of the user
    """

    def __init__(self, name: str, email: str):
        self.name: str = name
        self.email: str = email

    def __iter__(self):
        yield "name", self.name
        yield "email", self.email
