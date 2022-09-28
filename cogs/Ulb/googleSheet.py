# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from typing import Dict
from typing import Tuple

import disnake
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from .ulbUser import UlbUser
from bot import Bot


class GoogleSheetManagerNotLoadedError(Exception):
    """The Exception to be raise when the GoogleSheetManager class is used without have been loaded."""

    def __init__(self, *args: object) -> None:
        super().__init__("The GoogleSheetManager class need to be loaded with 'load()' before being used !")


class GoogleSheetInstantiationError(Exception):
    """The Exception to be raise when the GoogleSheetManager class is instantiated."""

    def __init__(self, *args: object) -> None:
        super().__init__("The GoogleSheetManager class cannot be instantiated, but only used as a class.")


class GoogleSheetManager:
    """Represent the GoogleSheetManager.

    This class is only used as a class and should not be instantiated

    Properties
    ----------
    loaded: `bool`
        `True` if the class has been loaded. `False` otherwise

    Classmethods
    ------------
    load(bot: Bot):
        Load the GoogleSheet data. This need to be called before using the other methods
    set_user(user_id: `int`, name: `str`, email: `str`):
        Add or update an user to the database
    set_guild(guild_id: `int`, role_id: `int`):
        Add or update an guild to the database
    """

    _scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    _users_ws: gspread.Worksheet = None
    _guilds_ws: gspread.Worksheet = None
    _loaded = False

    def __init__(self) -> None:
        raise GoogleSheetInstantiationError

    @property
    def loaded(cls) -> bool:
        return cls._loaded

    @classmethod
    def load(cls, bot: Bot) -> Tuple[Dict[disnake.Guild, disnake.Role], Dict[disnake.User, UlbUser]]:
        """Load the data from the google sheet.

        Returns
        -------
        `Tuple[Dict[disnake.Guild, disnake.Role], Dict[disnake.User, UlbUser]]`
            Tuple of (Guilds,Users) with:
            - Guild: `Dict[disnake.Guild, disnake.Role]`
            - Users: `Dict[disnake.User, UlbUser]]`
        """
        # cred_dict = json.load(open("cogs/Ulb/google_sheet_cred.json", "rb"))
        cred_dict = {}
        cred_dict["type"] = os.getenv("GS_TYPE")
        cred_dict["project_id"] = os.getenv("GS_PROJECT_ID")
        cred_dict["auth_uri"] = os.getenv("GS_AUTHOR_URI")
        cred_dict["token_uri"] = os.getenv("GS_TOKEN_URI")
        cred_dict["auth_provider_x509_cert_url"] = os.getenv("GS_AUTH_PROV")
        cred_dict["client_x509_cert_url"] = os.getenv("GS_CLIENT_CERT_URL")
        cred_dict["private_key"] = os.getenv("GS_PRIVATE_KEY")
        cred_dict["private_key_id"] = os.getenv("GS_PRIVATE_KEY_ID")
        cred_dict["client_email"] = os.getenv("GS_CLIENT_EMAIL")
        cred_dict["client_id"] = os.getenv("GS_CLIENT_ID")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, cls._scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(os.getenv("GOOGLE_SHEET_URL"))
        cls.users_ws = sheet.worksheet("users")
        cls.guilds_ws = sheet.worksheet("guilds")

        logging.info("[GoogleSheet] Google sheet opened. Loading data...")

        # Load guilds
        guilds = {}
        for guild_data in cls.guilds_ws.get_all_records():
            guild = bot.get_guild(guild_data.get("guild_id", int))
            if guild:
                role = guild.get_role(guild_data.get("role_id", int))
                if role:
                    guilds.setdefault(guild, role)
                    logging.debug(
                        f"[GoogleSheet] Role {role.name}:{role.id} loaded from guild {guild.name}:{guild.id} "
                    )
                else:
                    logging.warning(
                        f"[GoogleSheet] Not able to find role from id={guild_data.get('role_id', int)} in guild {guild.name}:{guild.id}."
                    )
            else:
                logging.warning(f"[GoogleSheet] Not able to find guild from id={guild_data.get('guild_id', int)}.")
        logging.info(f"[GoogleSheet] Found {len(guilds)} guilds.")

        # Load users
        users = {}
        for user_data in cls.users_ws.get_all_records():
            user = bot.get_user(user_data.get("user_id", int))
            if user:
                users.setdefault(user, UlbUser(user_data.get("name", str), user_data.get("email", str)))
                logging.debug(
                    f"[GoogleSheet] User {user.name}:{user.id} loaded with name={user_data.get('name')} and email={user_data.get('email')}"
                )
            else:
                logging.warning(f"[GoogleSheet] Not able to find user from id={user_data.get('user_id',int)}.")
        logging.info(f"[GoogleSheet] Found {len(users)} users.")

        cls._loaded = True
        return (guilds, users)

    @classmethod
    async def _set_user_task(cls, user_id: int, name: str, email: str):
        """Coroutine task called by `set_user()` to add or update ulb user informations on the google sheet

        Parameters
        ----------
        user_id : `int`
            The user id
        name : `str`
            The name
        email : `str`
            The email address
        """
        user_cell: gspread.cell.Cell = cls.users_ws.find(str(user_id), in_column=1)
        await asyncio.sleep(0.1)
        if user_cell:
            logging.debug(f"[GoogleSheet] {user_id=} found in WS at row={user_cell.row}")
            cls.users_ws.update_cell(user_cell.row, 2, name)
            await asyncio.sleep(0.1)
            cls.users_ws.update_cell(user_cell.row, 3, email)
            logging.debug(f"[GoogleSheet] {user_id=} updated with {name=} and {email=}")
        else:
            logging.debug(f"[GoogleSheet] {user_id=} not found in WS")
            cls.users_ws.append_row(values=[str(user_id), name, email])
            logging.debug(f"[GoogleSheet] {user_id=} added with {name=} and {email=}")

    @classmethod
    def set_user(cls, user_id: int, name: str, email: str):
        """Add or update ulb user informations on the google sheet.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        user_id : `int`
            The user id
        name : `str`
            The name
        email : `str`
            The email address
        """
        asyncio.create_task(cls._set_user_task(user_id, name, email))

    @classmethod
    async def _set_guild_task(cls, guild_id: int, role_id: int):
        """Coroutine task called by `set_guilds()` to add or update ulb guild informations on the google sheet.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        guild_id : `int`
            Guild id
        role_id : `int`
            Ulb Role id
        """
        guild_cell: gspread.cell.Cell = cls.guilds_ws.find(str(guild_id), in_column=1)
        await asyncio.sleep(0.1)
        if guild_cell:
            logging.debug(f"[GoogleSheet] {guild_id=} found in WS.")
            cls.guilds_ws.update_cell(guild_cell.row, 2, str(role_id))
            logging.debug(f"[GoogleSheet] {guild_id=} update with {role_id=}.")
        else:
            logging.debug(f"[GoogleSheet] {guild_id=} not found in WS.")
            cls.guilds_ws.append_row(values=[str(guild_id), str(role_id)])
            logging.debug(f"[GoogleSheet] {guild_id=} added with {role_id=}.")

    @classmethod
    def set_guild(cls, guild_id: int, role_id: int):
        """Add or update ulb guild informations on the google sheet.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        guild_id : `int`
            Guild id
        role_id : `int`
            Ulb Role id
        """
        asyncio.create_task(cls._set_guild_task(guild_id, role_id))
