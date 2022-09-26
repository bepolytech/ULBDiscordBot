# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from typing import Tuple

import gspread

from .ULBUser import ULBUser
from bot import Bot


class GoogleSheetManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        sheet = gspread.service_account(filename="cogs/ULB/google_sheet_cred.json").open_by_url(
            os.getenv("GOOGLE_SHEET_URL")
        )
        self.users = sheet.worksheet("users")
        self.guilds = sheet.worksheet("guilds")

    def load(self) -> Tuple[dict, dict]:
        guilds = {}
        for guild_data in self.guilds.get_all_records():
            guild = self.bot.get_guild(guild_data.get("guild_id", int))
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
        for user_data in self.users.get_all_records():
            user = self.bot.get_user(user_data.get("user_id", int))
            if user:
                users.setdefault(user, ULBUser(user_data.get("name", str), user_data.get("email", str)))
                logging.debug(
                    f"User {user.name}:{user.id} loaded with name={user_data.get('name')} and email={user_data.get('email')}"
                )
            else:
                logging.warning(f"Unable to find user from id={user_data.get('user_id',int)}.")
        logging.info(f"Loaded {len(users)} users.")

        return (guilds, users)

    async def set_user_task(self, user_id: int, name: str, email: str):
        user_cell: gspread.cell.Cell = self.users.find(str(user_id), in_column=1)
        if user_cell:
            self.users.update_cell(user_cell.row, 2, name)
            self.users.update_cell(user_cell.row, 3, email)
        else:
            self.users.append_row(values=[str(user_id), name, email])

    def set_user(self, user_id: int, name: str, email: str):
        asyncio.create_task(self.set_user_task(user_id, name, email))

    async def set_guild_task(self, guild_id: int, role_id: int):
        guild_cell: gspread.cell.Cell = self.guilds.find(str(guild_id), in_column=1)
        if guild_cell:
            self.guilds.update_cell(guild_cell.row, 2, str(role_id))
        else:
            self.guilds.append_row(values=[str(guild_id), str(role_id)])

    def set_guild(self, guild_id: int, role_id: int):
        asyncio.create_task(self.set_guild_task(guild_id, role_id))
