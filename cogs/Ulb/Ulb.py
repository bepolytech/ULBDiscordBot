# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from typing import Dict

import disnake
from disnake import ApplicationCommandInteraction
from disnake.client import HTTPException
from disnake.ext import commands

from .googleSheet import GoogleSheetManager
from .registrationForm import RegistrationForm
from .ulbUser import UlbUser
from bot import Bot


class Ulb(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot
        self.ulb_guilds: Dict[disnake.Guild, disnake.Role] = {}
        self.ulb_users: Dict[disnake.User, UlbUser] = {}

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        (self.ulb_guilds, self.ulb_users) = GoogleSheetManager.load(self.bot)
        RegistrationForm.setup(self)
        logging.info("[Cog:Ulb] Ready")

    async def wait_data(self) -> None:
        if not GoogleSheetManager.loaded:
            logging.debug("[Cog:Ulb] Waiting for data to be load from google sheet...")
            await asyncio.sleep(1)
        while not GoogleSheetManager.loaded:
            await asyncio.sleep(1)

    async def wait_setup(self) -> None:
        if not GoogleSheetManager.loaded:
            await self.wait_data()
        if not RegistrationForm.set:
            logging.debug("[Cog:Ulb]  Waiting for registrationForm to be set...")
            await asyncio.sleep(1)
        while not RegistrationForm.set:
            await asyncio.sleep(1)

    @commands.slash_command(name="email", description="Vérifier son adresse mail ULB.")
    async def email(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.wait_setup()

        await RegistrationForm.new(inter)

    @commands.slash_command(name="role", default_member_permissions=disnake.Permissions.all())
    async def roles(self, inter: ApplicationCommandInteraction):
        pass

    @roles.sub_command(name="setup", description="Sélectionner le role ULB de ce serveur.")
    async def roles_setup(
        self, inter: ApplicationCommandInteraction, role_ulb: disnake.Role = commands.Param(description='Le role "ULB"')
    ):
        await inter.response.defer(ephemeral=True)
        await self.wait_data()

        GoogleSheetManager.set_guild(inter.guild.id, role_ulb.id)
        self.ulb_guilds[inter.guild] = role_ulb

        embed = disnake.Embed(
            title="Setup du role ULB du servers",
            description=f"Role **ULB** : {role_ulb.mention}",
            color=disnake.Color.green(),
        ).set_footer(text='Utilise "/role_update" pour mettre à jour les roles des membres de ce serveur.')

        roles_warning = []
        if inter.guild.default_role.permissions.change_nickname:
            roles_warning.append(inter.guild.default_role.mention)
        if role_ulb.permissions.change_nickname:
            roles_warning.append(role_ulb.mention)
        if roles_warning:
            embed.add_field(
                name="⚠️",
                value=" et ".join(roles_warning)
                + " ont la permission de changer leur propre pseudo.\nRetirez ces permissions si vous voulez que les membres soit obligés de garder leur vrai nom.",
            )

        # TODO add bot role permissions to tell which role it can edit nick

        await inter.edit_original_message(embed=embed)

    @roles.sub_command(
        name="update",
        description="Mettre à jour les roles des members de ce serveur (uniquement ajoute les nouveaux membres).",
    )
    async def roles_update(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.wait_data()

        if inter.guild not in self.ulb_guilds.keys():
            await inter.edit_original_message(
                embed=disnake.Embed(
                    description="""Le role **ULB** de ce serveur n'est pas encore setup ! Utilise **"/role setup"** pour le sélectionner.""",
                    color=disnake.Color.orange(),
                )
            )

        ulb_role = self.ulb_guilds.get(inter.guild)
        if ulb_role:
            for member in inter.guild.members:
                if member in self.ulb_users.keys():
                    ulb_user = self.ulb_users.get(member)
                    if ulb_role not in member.roles:
                        try:
                            await member.add_roles(ulb_role)
                        except HTTPException as ex:
                            logging.error(
                                f'[Cog:Ulb] Error adding ulb role "{ulb_role.name}:{ulb_role.id}" from guild "{inter.guild.name}:{inter.guild.id}" to ulb user "{member.name}:{member.id}": {ex}'
                            )
                    if member.display_name != ulb_user.name:
                        try:
                            await member.edit(nick=f"{ulb_user.name}")
                        except HTTPException as ex:
                            logging.warning(
                                f'[Cog:Ulb] Error editing user "{member.name}:{member.id}" nick to "{ulb_user.name}": {ex}'
                            )
            await inter.edit_original_message(
                embed=disnake.Embed(description="Mise à jour finie !", color=disnake.Color.green())
            )
        else:
            logging.error(
                f"[Cog:Ulb] Not able to find ulb role from id={self.ulb_guilds.get(inter.guild)} for guild {inter.guild.name}:{inter.guild.id}."
            )
            await inter.edit_original_message(
                embed=disnake.Embed(
                    description=""""Impossible de trouver le role ULB.\nSi celui-ci a été supprimé, il est nécessaire d'en sélectionner un autre avec **"/role setup"**.""",
                    color=disnake.Color.orange(),
                )
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        await self.wait_data()

        # Either ask to register, or autmotically add role and real name for user joining ulb guild
        if member.guild in self.ulb_guilds.keys():
            if member not in self.ulb_users.keys():
                await member.send(
                    embed=disnake.Embed(
                        title=f"__Bienvenu sur le server **{member.guild.name}**__",
                        description="""Ce serveur est reservé aux membre de l'ULB. Pour acceder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande **"/email"**.""",
                        color=disnake.Color.teal(),
                    ).set_thumbnail(url=self.bot.BEP_image)
                )
            else:
                try:
                    await member.add_roles(self.ulb_guilds.get(member.guild))
                except HTTPException as ex:
                    logging.error(
                        f'[Cog:Ulb] Error adding ulb role "{self.ulb_guilds.get(member.guild).name}:{self.ulb_guilds.get(member.guild).id}" from guild "{member.guild.name}:{member.guild.id}" to ulb user "{member.name}:{member.id}": {ex}'
                    )
                try:
                    await member.edit(nick=f"{self.ulb_users.get(member).name}")
                except HTTPException as ex:
                    logging.warning(
                        f'[Cog:Ulb] Error editing user "{member.name}:{member.id}" nick to "{self.ulb_users.get(member).name}": {ex}'
                    )

    @commands.Cog.listener("on_guild_join")
    async def on_member_join(self, guild: disnake.Guild):
        # Autodetect ULB role for guild that follow the ULB guild template
        if os.getenv("GUILD_TEMPLATE_CODE") in [t.code for t in await guild.templates()]:
            for role in guild.roles:
                if role.name == "ULB":
                    self.ulb_guilds[guild] = role
                    logging.info(
                        f"[Cog:Ulb] New guild following ULB template joined. Role {role.name}:{role.id} automatically set as ULB role."
                    )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
