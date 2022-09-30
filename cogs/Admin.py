# -*- coding: utf-8 -*-
import os
from typing import List

import disnake
from disnake.ext import commands

from bot import Bot
from classes import Database
from classes import utils
from classes.registration import AdminAddUserModal
from classes.registration import AdminEditUserModal


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot

    @commands.slash_command(
        name="update",
        description="Forcer la mise à jour de la database et des serveurs.",
        guilds=[int(os.getenv("ADMIN_GUILD_ID"))],
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        Database.load(self.bot)
        await utils.update_all_guilds()
        await inter.edit_original_response(
            embed=disnake.Embed(description="All servers updated !", color=disnake.Color.green())
        )

    @commands.slash_command(
        name="user",
        guilds=[int(os.getenv("ADMIN_GUILD_ID"))],
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def user(self, inter):
        pass

    @user.sub_command(name="add", description="Ajouter un utilisateur discord.")
    async def user_set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'id discord de l'utilisateur à ajouter.", min_length=18, max_length=18
        ),
    ):
        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(AdminAddUserModal(user))

    # TODO: put all fields optional and added autocomplete to all of them + error if no one is provided
    @user.sub_command(name="edit", description="Editer un utilisateur ULB.")
    async def user_edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'id discord de l'utilisateur ULB à éditer.", min_length=18, max_length=18
        ),
    ):
        user = self.bot.get_user(int(user_id))

        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        user_data = Database.ulb_users.get(user)
        if not user_data:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur ULB avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(AdminEditUserModal(user))

    # TODO: put all fields optional and added autocomplete to all of them + error if no one is provided
    @user.sub_command(name="info", description="Voir les informations d'un utilisateur enregistré")
    async def user_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'id discord de l'utilisateur ULB dont vous voulez voir les informations.",
            min_length=18,
            max_length=18,
        ),
    ):
        user = self.bot.get_user(int(user_id))
        user_data = Database.ulb_users.get(user)
        guilds_name: List[str] = [f"`{guild.name}`" for guild in Database.ulb_guilds.keys() if user in guild.members]
        await inter.response.send_message(
            embed=disnake.Embed(
                title="Info de l'utilisateur",
                description=f"**User id :** `{user_id}`\n**Nom :** {user_data.name}\n**Adresse email :** *{user_data.email}*\n**ULB serveurs :** {','.join(guilds_name) if guilds_name else '*Aucun...*'}",
                color=disnake.Colour.green(),
            ),
            ephemeral=True,
        )

    # TODO: add autocomplete for name
    @user.sub_command(name="delete", description="Supprimer un utilisateur enregistré")
    async def user_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'id discord de l'utilisateur ULB à supprimer.", min_length=18, max_length=18
        ),
        name: str = commands.Param(description="Le nom ULB de l'utilisateur ULB à supprimer (pour confirmation)"),
    ):
        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )
            return

        user_data = Database.ulb_users.get(user)
        if not user_data:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur ULB avec user id = {user_id}", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )
            return

        if user_data.name.lower() != name.lower():
            await inter.response.send_message(
                embed=disnake.Embed(description="L'id et le nom ne correspondent pas...", color=disnake.Color.red())
            )
        else:
            Database.delete_user(user)
            await inter.response.send_message(
                embed=disnake.Embed(
                    title=f"L'utilisateur à bien été supprimé !",
                    description=f"**User id :** `{user_id}`\n**Nom :** {user_data.name}\n**Adresse email :** *{user_data.email}*",
                    color=disnake.Color.green(),
                ),
                ephemeral=True,
            )

    @user_edit.autocomplete("user_id")
    @user_info.autocomplete("user_id")
    @user_delete.autocomplete("user_id")
    async def user_id_autocomplete(self, inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [str(user.id) for user in Database.ulb_users.keys() if str(user.id).startswith(user_input)]


def setup(bot: commands.InteractionBot):

    bot.add_cog(Admin(bot))
