# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from typing import Dict
from typing import Optional

import disnake
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from bot import Bot


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


class UlbGuild:
    """Represent an UlbGuild

    Parameters
    ----------
    role: `disnake.Role`
        The @ULB role of the guild
    rename: `bool`
        If the guild want to force rename of not
    """

    def __init__(self, role: disnake.Role, rename: bool = True) -> None:
        self.role: disnake.Role = role
        self.rename: bool = rename


class DatabaseNotLoadedError(Exception):
    """The Exception to be raise when the DataBase class is used without have been loaded."""

    def __init__(self, *args: object) -> None:
        super().__init__("The DataBase class need to be loaded with 'load()' before being used !")


class DatabaseInstantiationError(Exception):
    """The Exception to be raise when the DataBase class is instantiated."""

    def __init__(self, *args: object) -> None:
        super().__init__("The DataBase class cannot be instantiated, but only used as a class.")


class Database:
    """Represent the DataBase.

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
    _sheet: gspread.Spreadsheet = None
    _users_ws: gspread.Worksheet = None
    _guilds_ws: gspread.Worksheet = None
    ulb_guilds: Dict[disnake.Guild, UlbGuild] = None
    ulb_users: Dict[disnake.User, UlbUser] = None
    _loaded = False

    def __init__(self) -> None:
        raise DatabaseInstantiationError

    @property
    def loaded(cls) -> bool:
        return cls._loaded

    @classmethod
    async def load(cls, bot: Bot) -> bool:
        """Load the data from the google sheet.

        Returns
        -------
        `Tuple[Dict[disnake.Guild, disnake.Role], Dict[disnake.User, UlbUser]]`
            Tuple of (Guilds,Users) with:
            - Guild: `Dict[disnake.Guild, disnake.Role]`
            - Users: `Dict[disnake.User, UlbUser]]`
        """
        try:
            # First time this is call, we need to load the credentials and the sheet
            if not cls._sheet:
                cred_dict = {}
                cred_dict["type"] = os.getenv("GS_TYPE")
                cred_dict["project_id"] = os.getenv("GS_PROJECT_ID")
                cred_dict["auth_uri"] = os.getenv("GS_AUTHOR_URI")
                cred_dict["token_uri"] = os.getenv("GS_TOKEN_URI")
                cred_dict["auth_provider_x509_cert_url"] = os.getenv("GS_AUTH_PROV")
                cred_dict["client_x509_cert_url"] = os.getenv("GS_CLIENT_CERT_URL")
                cred_dict["private_key"] = os.getenv("GS_PRIVATE_KEY").replace(
                    "\\n", "\n"
                )  # Python add a '\' before any '\n' when loading a str
                cred_dict["private_key_id"] = os.getenv("GS_PRIVATE_KEY_ID")
                cred_dict["client_email"] = os.getenv("GS_CLIENT_EMAIL")
                cred_dict["client_id"] = int(os.getenv("GS_CLIENT_ID"))
                creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, cls._scope)
                cls._client = gspread.authorize(creds)
                logging.info("[Database] Google sheet credentials loaded.")

                # Open google sheet
                cls._sheet = cls._client.open_by_url(os.getenv("GOOGLE_SHEET_URL"))
                cls._users_ws = cls._sheet.worksheet("users")
                cls._guilds_ws = cls._sheet.worksheet("guilds")

                logging.info("[Database] Spreadsheed loaded")
        except (ValueError, gspread.exceptions.SpreadsheetNotFound, gspread.exceptions.WorksheetNotFound) as err:
            await bot.send_error_log(bot.tracebackEx(err))
            return

        logging.info("[Database] Loading data...")

        # Load guilds
        cls.ulb_guilds = {}
        for guild_data in cls._guilds_ws.get_all_records():
            guild: disnake.Guild = bot.get_guild(guild_data.get("guild_id", int))
            if guild:
                role: disnake.Role = guild.get_role(guild_data.get("role_id", int))
                rename: bool = True if guild_data.get("rename", str) == "TRUE" else False
                if role:
                    cls.ulb_guilds.setdefault(guild, UlbGuild(role, rename))
                    logging.trace(
                        f"[Database] Role {role.name}:{role.id} loaded from guild {guild.name}:{guild.id} with {rename=}"
                    )
                else:
                    logging.warning(
                        f"[Database] Not able to find role from id={guild_data.get('role_id', int)} in guild {guild.name}:{guild.id}."
                    )
            else:
                logging.warning(f"[GoogleSheet] Not able to find guild from id={guild_data.get('guild_id', int)}.")
        logging.info(f"[Database] Found {len(cls.ulb_guilds)} guilds.")

        # Load users
        cls.ulb_users = {}
        for user_data in cls._users_ws.get_all_records():
            user = bot.get_user(user_data.get("user_id", int))
            if user:
                cls.ulb_users.setdefault(user, UlbUser(user_data.get("name", str), user_data.get("email", str)))
                logging.trace(
                    f"[Database] User {user.name}:{user.id} loaded with name={user_data.get('name')} and email={user_data.get('email')}"
                )
            else:
                logging.warning(f"[Database] Not able to find user from id={user_data.get('user_id',int)}.")
        logging.info(f"[Database] Found {len(cls.ulb_users)} users.")

        cls._loaded = True

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
        user_cell: gspread.cell.Cell = cls._users_ws.find(str(user_id), in_column=1)
        await asyncio.sleep(0.1)
        if user_cell:
            logging.debug(f"[Database] {user_id=} found")
            cls._users_ws.update_cell(user_cell.row, 2, name)
            await asyncio.sleep(0.1)
            cls._users_ws.update_cell(user_cell.row, 3, email)
            logging.info(f"[Database] {user_id=} updated with {name=} and {email=}")
        else:
            logging.debug(f"[Database] {user_id=} not found")
            cls._users_ws.append_row(values=[str(user_id), name, email])
            logging.info(f"[Database] {user_id=} added with {name=} and {email=}")

    @classmethod
    def set_user(cls, user: disnake.User, name: str, email: str):
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
        if not cls._loaded:
            raise DatabaseNotLoadedError
        cls.ulb_users[user] = UlbUser(name, email)
        asyncio.create_task(cls._set_user_task(user.id, name, email))

    @classmethod
    async def _delete_user_task(cls, user_id: int):
        """Coroutine task called by `delete_user()` to delete ulb user informations from the google sheet

        Parameters
        ----------
        user_id : `int`
            The user id
        """
        user_cell: gspread.cell.Cell = cls._users_ws.find(str(user_id), in_column=1)
        await asyncio.sleep(0.1)
        logging.trace(f"[Database] {user_id=} found")
        cls._users_ws.delete_row(user_cell.row)
        await asyncio.sleep(0.1)
        logging.info(f"[Database] {user_id=} deleted.")

    @classmethod
    def delete_user(cls, user: disnake.User):
        """Delete a given ulb user.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        user : `disnake.User`
            The user to delete
        """
        if not cls._loaded:
            raise DatabaseNotLoadedError
        cls.ulb_users.pop(user)
        asyncio.create_task(cls._delete_user_task(user.id))

    @classmethod
    async def _set_guild_task(cls, guild_id: int, role_id: int, rename: bool):
        """Coroutine task called by `set_guilds()` to add or update ulb guild informations on the google sheet.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        guild_id : `int`
            Guild id
        role_id : `int`
            Ulb Role id
        """
        guild_cell: gspread.cell.Cell = cls._guilds_ws.find(str(guild_id), in_column=1)
        await asyncio.sleep(0.1)
        if guild_cell:
            logging.debug(f"[Database] {guild_id=} found.")
            cls._guilds_ws.update_cell(guild_cell.row, 2, str(role_id))
            cls._guilds_ws.update_cell(guild_cell.row, 3, rename)
            logging.info(f"[Database] {guild_id=} update with {role_id=} and {rename=}.")
        else:
            logging.debug(f"[Database] {guild_id=} not found.")
            cls._guilds_ws.append_row(values=[str(guild_id), str(role_id), rename])
            logging.info(f"[Database] {guild_id=} added with {role_id=} and {rename=}.")

    @classmethod
    def set_guild(cls, guild: disnake.Guild, role: disnake.Role, rename: bool):
        """Add or update ulb guild informations on the google sheet.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        guild_id : `int`
            Guild id
        role_id : `int`
            Ulb Role id
        """
        if not cls._loaded:
            raise DatabaseNotLoadedError
        cls.ulb_guilds[guild] = UlbGuild(role, rename)
        asyncio.create_task(cls._set_guild_task(guild.id, role.id, rename))

    @classmethod
    async def _delete_guild_task(cls, guild_id: int):
        """Coroutine task called by `delete_guild()` to delete guild informations from the google sheet

        Parameters
        ----------
        guild_id : `int`
            The guild id
        """
        guild_cell: gspread.cell.Cell = cls._guilds_ws.find(str(guild_id), in_column=1)
        await asyncio.sleep(0.1)
        logging.trace(f"[Database] {guild_id=} found")
        cls._guilds_ws.delete_row(guild_cell.row)
        await asyncio.sleep(0.1)
        logging.info(f"[Database] {guild_id=} deleted.")

    @classmethod
    def delete_guild(cls, guild: disnake.Guild):
        """Delete a given ulb guild.

        It create a task without waiting for it to end, in order to not decrease the global performance of the Bot.

        Parameters
        ----------
        guild : `disnake.Guild`
            The guild to delete
        """
        if not cls._loaded:
            raise DatabaseNotLoadedError
        cls.ulb_guilds.pop(guild)
        asyncio.create_task(cls._delete_guild_task(guild.id))

    @classmethod
    def get_user_by_name(self, name: str) -> Optional[disnake.User]:
        for user, userdata in self.ulb_users.items():
            if userdata.name == name:
                return user
        return None

    @classmethod
    def get_user_by_email(self, email: str) -> Optional[disnake.User]:
        for user, userdata in self.ulb_users.items():
            if userdata.email == email:
                return user
        return None
