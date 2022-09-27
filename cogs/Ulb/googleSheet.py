# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import os
from typing import Dict
from typing import Tuple

import disnake
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from .ULBUser import ULBUser
from bot import Bot


class GoogleSheetManager:

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    data = json.load(open("cogs/Ulb/google_sheet_cred.json", "rb"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(data, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(os.getenv("GOOGLE_SHEET_URL"))
    users = sheet.worksheet("users")
    guilds = sheet.worksheet("guilds")

    loaded = False

    @classmethod
    def load(cls, bot: Bot) -> Tuple[Dict[disnake.Guild, disnake.Role], Dict[disnake.User, ULBUser]]:
        """Load the data from the google sheet.

        Returns
        -------
        `Tuple[Dict[disnake.Guild, disnake.Role], Dict[disnake.User, ULBUser]]`
            Tuple of (Guilds,Users) with:
            - Guild: `Dict[disnake.Guild, disnake.Role]`
            - Users: `Dict[disnake.User, ULBUser]]`
        """
        guilds = {}
        for guild_data in cls.guilds.get_all_records():
            guild = bot.get_guild(guild_data.get("guild_id", int))
            if guild:
                role = guild.get_role(guild_data.get("role_id", int))
                if role:
                    guilds.setdefault(guild, role)
                    logging.debug(f"Role {role.name}:{role.id} loaded from guild {guild.name}:{guild.id} ")
                else:
                    logging.warning(
                        f"Unable to find role from id={guild_data.get('role_id', int)} in guild {guild.name}:{guild.id}."
                    )
            else:
                logging.warning(f"Unable to find guild from id={guild_data.get('guild_id', int)}.")
        logging.info(f"Loaded {len(guilds)} guilds.")

        users = {}
        for user_data in cls.users.get_all_records():
            user = bot.get_user(user_data.get("user_id", int))
            if user:
                users.setdefault(user, ULBUser(user_data.get("name", str), user_data.get("email", str)))
                logging.debug(
                    f"User {user.name}:{user.id} loaded with name={user_data.get('name')} and email={user_data.get('email')}"
                )
            else:
                logging.warning(f"Unable to find user from id={user_data.get('user_id',int)}.")
        logging.info(f"Loaded {len(users)} users.")
        cls.loaded = True
        return (guilds, users)

    @classmethod
    async def _set_user_task(cls, user_id: int, name: str, email: str):
        user_cell: gspread.cell.Cell = cls.users.find(str(user_id), in_column=1)
        await asyncio.sleep(0.1)
        if user_cell:
            cls.users.update_cell(user_cell.row, 2, name)
            await asyncio.sleep(0.1)
            cls.users.update_cell(user_cell.row, 3, email)
        else:
            cls.users.append_row(values=[str(user_id), name, email])

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
        guild_cell: gspread.cell.Cell = cls.guilds.find(str(guild_id), in_column=1)
        await asyncio.sleep(0.1)
        if guild_cell:
            cls.guilds.update_cell(guild_cell.row, 2, str(role_id))
        else:
            cls.guilds.append_row(values=[str(guild_id), str(role_id)])

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
