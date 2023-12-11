# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from typing import Dict
from typing import Optional
#from flask_login import 

# TODO: compare with the database.py UlbUser class ?

class User: 
#class User(flask_login.UserMixin):
    """Represent an UlbUser

    Parameters
    ----------
    name: `str`
        The full name of the user
    email: `str`
        The ulb email address of the user
    site_lang: `str`
        The website language preferred of the user (default: 'fr')
    """
    def __init__(self, ulbid: str, name: str, email: str):
        self.ulbid: str = ulbid
        self.name: str = name
        self.email: str = email
        self.site_lang: str = "fr"
        self.is_authenticated = False # for flask_login
        self.is_active = True # for flask_login
        self.is_anonymous = False

    def get_id() -> str:
        # for flask_login
        return self.ulbid
