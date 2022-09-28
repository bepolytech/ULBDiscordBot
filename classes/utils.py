# -*- coding: utf-8 -*-
import logging

import disnake
from disnake import HTTPException

from .database import Database


class RoleNotInGuildError(Exception):
    def __init__(self, role: disnake.Role, guild: disnake.Guild) -> None:
        super().__init__(f"The role  {role.name}:{role.id} is not part of the guild {guild.name}:{guild.id}.")


async def update_member(member: disnake.Member, *, name: str = None, role: disnake.Role = None):
    """Update the role and nickname of a given member for the associated guild

    Parameters
    ----------
    member : `disnake.Member`
        The member to update
    name : `Optional[str]`
        The name to use instead of fetching the database
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database.

    Raise
    -----
    `RoleNotInGuildError`:
        Raised if the provided role in not in the roles of the associated guild
    """
    if not role:
        role = Database.ulb_guilds.get(member.guild)
    elif role not in member.guild.roles:
        raise RoleNotInGuildError(role, member.guild)
    if not name:
        name = Database.ulb_users.get(member).name

    try:
        await member.add_roles(role)
        logging.debug(f"[Utils:update_user] [User:{member.id}] Set role={role.id} on guild={member.id}")
    except HTTPException as ex:
        logging.error(
            f'[Utils:update_user] [User:{member.id}] Not able to add ulb role "{role.name}:{role.id}" from guild "{member.name}:{member.id}" to ulb user "{member.name}:{member.id}": {ex}'
        )
    try:
        await member.edit(nick=f"{name}")
        logging.debug(f"[Utils:update_user] [User:{member.id}] Set name on guild={member.id}")
    except HTTPException as ex:
        logging.warning(
            f'[Utils:update_user] [User:{member.id}] Not able to edit user "{member.name}:{member.id}" nick to "{name}": {ex}'
        )


async def update_user(user: disnake.User, *, name: str = None):
    """Update a given user across all ULB guilds

    Parameters
    ----------
    user : `disnake.User`
        The user to update
    name : `Optional[str]`
        The name to use instead of fetching the database.
    """
    if not name:
        name = Database.ulb_users.get(user).name
    for guild, role in Database.ulb_guilds.items():
        member = guild.get_member(user.id)
        if member:
            await update_member(member, name=name, role=role)


async def update_guild(guild: disnake.Guild, *, role: disnake.Role = None) -> None:
    """Update a given guilds.

    This add role and rename any registered member on the server. This don't affect not registered member.

    Parameters
    ----------
    guild : `disnake.Guild`
        The guild to update
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database
    """
    if not role:
        role = Database.ulb_guilds.get(guild)
    for member in guild.members:
        if member in Database.ulb_users.keys():
            await update_member(member, role=role)
