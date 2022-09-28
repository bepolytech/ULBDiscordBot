# -*- coding: utf-8 -*-
import os
from typing import List

import disnake
from disnake.ext import commands

from bot import Bot
from classes import GoogleSheetManager
from classes import update_guild
from classes.registrationForm import AdminAddUserModal
from classes.registrationForm import AdminEditUserModal


# TODO: add a ways to configure generic parameters (registration timeout, toke size, ...) directly with the discord bot commands (local .json file ?)


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot

    @commands.slash_command(name="admin", guilds=[int(os.getenv("ADMIN_GUILD_ID"))])
    async def admin(self, inter):
        pass

    @admin.sub_command_group(name="update")
    async def update(self, inter):
        pass

    @update.sub_command(name="database", description="Forcer la mise à jour de la database")
    async def update_database(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        GoogleSheetManager.load()
        await inter.edit_original_response(
            embed=disnake.Embed(description="Google sheet reloaded !", color=disnake.Color.green())
        )

    @update.sub_command(name="guilds", description="Mettre à jour tous les serveurs ULB.")
    async def update_guild(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        for guild, role in GoogleSheetManager.ulb_guilds.items():
            await update_guild(guild, role)

        await inter.edit_original_response(
            embed=disnake.Embed(description="All servers updated !", color=disnake.Color.green())
        )

    @admin.sub_command_group(name="user")
    async def user(self, inter):
        pass

    @user.sub_command(name="add", description="Ajouter un utilisateur discord.")  # Todo: separate ?
    async def user_set(self, inter: disnake.ApplicationCommandInteraction, user_id: str):
        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(AdminAddUserModal(user))

    @user.sub_command(name="edit", description="Editer un utilisateur ULB.")
    async def user_edit(self, inter: disnake.ApplicationCommandInteraction, user_id: str):
        user = self.bot.get_user(int(user_id))

        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        user_data = GoogleSheetManager.ulb_users.get(user)
        if not user_data:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur ULB avec user id = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(AdminEditUserModal(user))

    @user.sub_command(name="info", description="Voir les informations d'un utilisateur enregistré")
    async def user_info(self, inter: disnake.ApplicationCommandInteraction, user_id: str):
        user = self.bot.get_user(int(user_id))
        user_data = GoogleSheetManager.ulb_users.get(user)
        guilds_name: List[str] = [
            f"`{guild.name}`" for guild in GoogleSheetManager.ulb_guilds.keys() if user in guild.members
        ]
        await inter.response.send_message(
            embed=disnake.Embed(
                description=f"**User id :** `{user_id}`\n**Nom :** {user_data.name}\n**Adresse email :** *{user_data.email}*\n**ULB serveurs :** {','.join(guilds_name) if guilds_name else '*Aucun...*'}",
                color=disnake.Colour.green(),
            ),
            ephemeral=True,
        )

    @user.sub_command(name="delete", description="Supprimer un utilisateur enregistré")
    async def user_delete(self, inter: disnake.ApplicationCommandInteraction, user_id: str, name: str):

        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur discord avec user id = {user_id}", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )
            return

        user_data = GoogleSheetManager.ulb_users.get(user)
        if not user_data:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur ULB avec user id = {user_id}", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )
            return

        if user_data.name != name:
            await inter.response.send_message(
                embed=disnake.Embed(description="L'id et le nom ne correspondent pas...", color=disnake.Color.red())
            )
        else:
            GoogleSheetManager.delete_user(user)
            await inter.response.send_message(
                embed=disnake.Embed(description="L'utilisateur à bien été supprimé !'", color=disnake.Color.green()),
                ephemeral=True,
            )

    @user_edit.autocomplete("user_id")
    @user_info.autocomplete("user_id")
    @user_delete.autocomplete("user_id")
    async def user_id_autocomplete(self, inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [str(user.id) for user in GoogleSheetManager.ulb_users.keys() if str(user.id).startswith(user_input)]


def setup(bot: commands.InteractionBot):

    bot.add_cog(Admin(bot))
