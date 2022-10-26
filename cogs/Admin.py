# -*- coding: utf-8 -*-
import logging
import os
from typing import List

import disnake
from disnake.ext import commands

from bot import Bot
from classes import Database
from classes import utils
from classes import YearlyUpdate
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
        name="yearly-update",
        description="Retirer tous les utilisateur.rice.s en leur envoyant une notification par email",
        guilds=[int(os.getenv("ADMIN_GUILD_ID"))],
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def yearly_update(
        self,
        inter: disnake.ApplicationCommandInteraction,
        raison: str = commands.Param(
            description="""La raison de l'update ("Vérification annuelle" par default")""",
            default="Vérification annuelle",
        ),
    ):
        await YearlyUpdate.new(raison, inter)

    @commands.slash_command(
        name="user",
        guilds=[int(os.getenv("ADMIN_GUILD_ID"))],
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def user(self, inter):
        pass

    @user.sub_command(name="add", description="Ajouter un.e utilisateur.rice discord.")
    async def user_set(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'ID discord de l'utilisateur.rice à ajouter.", min_length=17, max_length=20
        ),
    ):
        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description=f"Pas d'utilisateur.rice discord avec User ID = {user_id}.", color=disnake.Colour.red()
                ),
                ephemeral=True,
            )

        await inter.response.send_modal(AdminAddUserModal(user))

    @user.sub_command(name="edit", description="Editer un.e utilisateur.rice ULB (un seul paramètre requis)")
    async def user_edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'ID discord de l'utilisateur.rice ULB à éditer.", min_length=17, max_length=20, default=None
        ),
        name: str = commands.Param(description="Le nom de l'utilisateur.rice ULB à éditer.", default=None),
        email: str = commands.Param(description="L'email de l'utilisateur.rice ULB à éditer.", default=None),
    ):
        if user_id:
            user = self.bot.get_user(int(user_id))
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'ID ne correspond à aucun.e utilisateur.rice Discord connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
            if user not in Database.ulb_users.keys():
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'ID ne correspond à aucun.e utilisateur.rice ULB.",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        elif name:
            user = Database.get_user_by_name(name)
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"Le nom ne correspond à aucun.e utilisateur.rice connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        elif email:
            user = Database.get_user_by_email(email)
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'email ne correspond à aucun.e utilisateur.rice connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        else:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title="Info de l'utilisateur.rice",
                    description=f"Spécifiez l'ID, le nom ou l'email dans la commande.",
                    color=disnake.Colour.orange(),
                ),
                ephemeral=True,
            )
            return
        await inter.response.send_modal(AdminEditUserModal(user))

    @user.sub_command(
        name="info", description="Voir les informations d'un.e utilisateur.rice enregistré.e (un seul paramètre requis)"
    )
    async def user_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'ID Discord de l'utilisateur.rice ULB dont vous voulez voir les informations.",
            min_length=18,
            max_length=18,
            default=None,
        ),
        name: str = commands.Param(
            description="Le nom de l'utilisateur.rice ULB dont vous voulez voir les informations.", default=None
        ),
        email: str = commands.Param(
            description="L'email de l'utilisateur.rice ULB dont vous voulez voir les informations.", default=None
        ),
    ):
        if user_id:
            user = self.bot.get_user(int(user_id))
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'ID ne correspond à aucun.e utilisateur.rice Discord connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
            if user not in Database.ulb_users.keys():
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'ID ne correspond à aucun.e utilisateur.rice ULB.",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        elif name:
            user = Database.get_user_by_name(name)
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"Le nom ne correspond à aucun.e utilisateur.rice connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        elif email:
            user = Database.get_user_by_email(email)
            if user == None:
                await inter.response.send_message(
                    embed=disnake.Embed(
                        title="Info de l'utilisateur.rice",
                        description=f"L'email ne correspond à aucun.e utilisateur.rice connu.e",
                        color=disnake.Colour.orange(),
                    ),
                    ephemeral=True,
                )
                return
        else:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title="Info de l'utilisateur.rice",
                    description=f"Spécifiez l'ID, le nom ou l'email dans la commande.",
                    color=disnake.Colour.orange(),
                ),
                ephemeral=True,
            )
            return
        user_data = Database.ulb_users.get(user)
        guilds_name: List[str] = [f"`{guild.name}`" for guild in Database.ulb_guilds.keys() if user in guild.members]
        await inter.response.send_message(
            embed=disnake.Embed(
                title="Info de l'utilisateur.rice",
                description=f"**User ID :** `{user.id}`\n**Nom :** {user_data.name}\n**Adresse email :** {f'*{user_data.email}*' if user_data.email else '*N/A*'}\n**ULB serveurs :** {','.join(guilds_name) if guilds_name else '*Aucun...*'}",
                color=disnake.Colour.green(),
            ),
            ephemeral=True,
        )

    @user.sub_command(name="delete", description="Supprimer un.e utilisateur.rice enregistré.e.")
    async def user_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_id: str = commands.Param(
            description="L'ID Discord de l'utilisateur.rice ULB à supprimer.", min_length=17, max_length=20
        ),
        name: str = commands.Param(description="Le nom ULB de l'utilisateur.rice ULB à supprimer (pour confirmation)"),
        remove_ulb: str = commands.Param(
            description="Retirer l'utilisateur.rice du role ULB dans tous les serveurs.", choices=["Oui", "Non"]
        ),
    ):
        await inter.response.defer(ephemeral=True)
        user = self.bot.get_user(int(user_id))
        if not user:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur.rice Discord avec User ID = {user_id}", color=disnake.Colour.red()
                )
            )
            return

        user_data = Database.ulb_users.get(user)
        if not user_data:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    description=f"Pas d'utilisteur.rice ULB avec User ID = {user_id}", color=disnake.Colour.red()
                )
            )
            return

        if user_data.name.lower() != name.lower():
            await inter.edit_original_response(
                embed=disnake.Embed(description="L'ID et le nom ne correspondent pas...", color=disnake.Color.red())
            )
        else:
            Database.delete_user(user)
            error_roles = []
            if remove_ulb == "Oui":
                for guild, guild_data in Database.ulb_guilds.items():
                    if user in guild.members:
                        member = guild.get_member(user.id)
                        if guild_data.role in member.roles:
                            try:
                                await member.remove_roles(guild_data.role)
                            except disnake.HTTPException:
                                error_roles.append(
                                    f"**{guild_data.role.name}:{guild_data.role.id}** du serveur **{guild.name}:{guild.id}**"
                                )
                                logging.error(
                                    f"[Cog:Admin] [Delete user {user.name}:{user.id}] Not able to remove role {guild_data.role.name}:{guild_data.role.id} of guild {guild.name}:{guild.id}."
                                )
                            if guild_data.rename and member.nick == user_data.name:
                                try:
                                    await member.edit(nick=None)
                                except disnake.HTTPException:
                                    logging.warning(
                                        f"[Cog:Admin] [Delete user {user.name}:{user.id}] Not able to remove nickname"
                                    )

            embed = disnake.Embed(
                title=f"L'utilisateur.rice à bien été supprimé.e !",
                description=f"**User ID :** `{user_id}`\n**Nom :** {user_data.name}\n**Adresse email :** *{user_data.email}*",
                color=disnake.Color.green(),
            )
            if error_roles:
                embed.add_field(
                    name="⚠️",
                    value="Les rôles @ULB des serveurs suivants n'ont pas pu être retirés :\n"
                    + "\n >".join(error_roles),
                )
            await inter.edit_original_response(
                embed=embed,
            )

    @user_edit.autocomplete("user_id")
    @user_info.autocomplete("user_id")
    @user_delete.autocomplete("user_id")
    async def user_id_autocomplete(self, inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [str(user.id) for user in Database.ulb_users.keys() if str(user.id).startswith(user_input)]

    @user_edit.autocomplete("name")
    @user_info.autocomplete("name")
    @user_delete.autocomplete("name")
    async def name_autocomplete(self, inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [
            str(userdata.name) for userdata in Database.ulb_users.values() if str(userdata.name).startswith(user_input)
        ]

    @user_edit.autocomplete("email")
    @user_info.autocomplete("email")
    async def email_autocomplete(self, inter: disnake.ApplicationCommandInteraction, user_input: str):
        return [
            str(userdata.email)
            for userdata in Database.ulb_users.values()
            if str(userdata.email).startswith(user_input) and userdata.email != "N/A"
        ]


def setup(bot: commands.InteractionBot):

    bot.add_cog(Admin(bot))
