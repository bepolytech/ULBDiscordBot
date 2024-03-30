# -*- coding: utf-8 -*-
import asyncio
import logging

import disnake
from disnake import HTTPException

from .database import Database


class RoleNotInGuildError(Exception):
    def __init__(self, role: disnake.Role, guild: disnake.Guild) -> None:
        super().__init__(f"The role  {role.name}:{role.id} is not part of the guild {guild.name}:{guild.id}.")


async def wait_data(inter: disnake.ApplicationCommandInteraction = None, timeout: int = None) -> bool:
    """Async sleep until Database is loaded

    Parameters
    ----------
    inter : disnake.ApplicationCommandInteraction, optional
        The inter to edit_original_response in case of timeout, by default None
    timeout : int, optional
        The timeout duration, by default None. Must be provide if inter is provided.

    Returns
    -------
    bool
        True if not timeout, False if timeout
    """
    if inter != None and timeout == None:
        logging.warning(
            f"[Utils:wait_data] timeout cannot be None if inter is provided at the same time. Timeout=30 is used instead."
        )
        timeout = 30
    if not Database.loaded:
        logging.trace("[Utils] Waiting for database to be loaded...")
        current_time = 0
        while not Database.loaded and (timeout == None or current_time < timeout):
            await asyncio.sleep(1)
            current_time += 1
        if not Database.loaded:
            logging.error("[Utils] Database load waiting timeout !")
            if inter != None:
                await inter.edit_original_response(
                    embed=disnake.Embed(
                        title="Commande temporairement inaccessible.",
                        description="Veuillez réessayer dans quelques instants.",
                        color=disnake.Color.orange(),
                    )
                )
            return False
    return True


async def update_member(member: disnake.Member, *, name: str = None, role: disnake.Role = None, rename: bool = None):
    """Update the role and nickname of a given member for the associated guild

    Parameters
    ----------
    member : `disnake.Member`
        The member to update
    name : `Optional[str]`
        The name to use instead of fetching the database
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database.
    rename : `Optional[bool]`
        Does the guild force rename or not

    Raise
    -----
    `RoleNotInGuildError`:
        Raised if the provided role in not in the roles of the associated guild
    """
    if role == None:
        role = Database.ulb_guilds.get(member.guild).role
    elif role not in member.guild.roles:
        raise RoleNotInGuildError(role, member.guild)
    if rename == None:
        rename = Database.ulb_guilds.get(member.guild).rename

    if rename:
        if name == None:
            name = Database.ulb_users.get(member).name
        if member.nick == None or member.nick != name:
            try:
                await member.edit(nick=f"{name}")
                logging.info(f"[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Set name={name}")
            except HTTPException as ex:
                logging.warning(
                    f'[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Not able to edit user "{member.name}:{member.id}" nick to "{name}": {ex}'
                )
    if role not in member.roles:
        try:
            await member.add_roles(role)
            logging.info(f"[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Set role={role.id}")
        except HTTPException as ex:
            logging.error(
                f'[Utils:update_user] [User:{member.id}] [Guild:{member.guild.id}] Not able to add ulb role "{role.name}:{role.id}" to ulb user "{member.name}:{member.id}": {ex}'
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
    if name == None:
        name = Database.ulb_users.get(user).name
    for guild, guild_data in Database.ulb_guilds.items():
        member = guild.get_member(user.id)
        if member:
            await update_member(member, name=name, role=guild_data.role, rename=guild_data.rename)


async def update_guild(guild: disnake.Guild, *, role: disnake.Role = None, rename: bool = None) -> None:
    """Update a given guilds.

    This add role and rename any registered member on the server. This don't affect not registered member.

    Parameters
    ----------
    guild : `disnake.Guild`
        The guild to update
    role : `Optional[disnake.Role]`
        The role to use instead of fetching the database
    rename : `Optional[bool]`
        Does the guild force rename or not
    """
    if role == None:
        role = Database.ulb_guilds.get(guild).role
    if rename == None:
        rename = Database.ulb_guilds.get(guild).rename
    for member in guild.members:
        if member in Database.ulb_users.keys():
            await update_member(member, role=role, rename=rename)


async def update_all_guilds(force_rename: bool = False) -> None:
    """Update all guilds.

    This create tasks to do it.
    """
    logging.info("[Utils] Checking all guilds...")
    await asyncio.gather(
        *[
            update_guild(guild, role=guild_data.role, rename=force_rename if guild_data.rename else guild_data.rename) # force rename users only if both the guild has rename enabled and the admin set the update to force rename true
            for guild, guild_data in Database.ulb_guilds.items()
        ]
    )
    logging.info("[Utils] All guilds checked !")


async def remove_user(user: disnake.User) -> None:
    """Remove a user from the database and remove role / nickname for all guilds

    Parameters
    ----------
    user : disnake.User
        The user to remove
    """
    user_data = Database.ulb_users.get(user)
    Database.delete_user(user)
    for guild, guild_data in Database.ulb_guilds.items():
        if user in guild.members:
            member = guild.get_member(user.id)
            if guild_data.role in member.roles:
                try:
                    await member.remove_roles(guild_data.role)
                except disnake.HTTPException:
                    logging.error(
                        f"[Cog:Admin] [Delete user {user.name}:{user.id}] Not able to remove role {guild_data.role.name}:{guild_data.role.id} of guild {guild.name}:{guild.id}."
                    )
                if guild_data.rename and member.nick == user_data.name:
                    try:
                        await member.edit(nick=None)
                    except disnake.HTTPException:
                        logging.warning(f"[Cog:Admin] [Delete user {user.name}:{user.id}] Not able to remove nickname")
