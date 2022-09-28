# -*- coding: utf-8 -*-
import asyncio
import logging
import os

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from bot import Bot
from classes import *


class Ulb(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot
        self.ulb_guil_template_url: str = os.getenv("GUILD_TEMPLATE_URL")

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        Database.load(self.bot)
        RegistrationForm.setup(self)
        logging.info("[Cog:Ulb] Ready")

    async def wait_data(self) -> None:
        """Async sleep until GoogleSheet is loaded"""
        if not Database.loaded:
            logging.debug("[Cog:Ulb] Waiting for data to be load from google sheet...")
            await asyncio.sleep(1)
        while not Database.loaded:
            await asyncio.sleep(1)

    async def wait_setup(self) -> None:
        """Async sleep until GoogleSheet is loaded and RegistrationForm is set"""
        if not Database.loaded:
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

    @commands.slash_command(
        name="setup",
        description="Sélectionner le role ULB de ce serveur.",
        default_member_permissions=disnake.Permissions.all(),
    )
    async def setup(
        self, inter: ApplicationCommandInteraction, role_ulb: disnake.Role = commands.Param(description='Le role "ULB"')
    ):
        await inter.response.defer(ephemeral=True)
        await self.wait_data()

        Database.set_guild(inter.guild, role_ulb)
        embed = disnake.Embed(
            title="Setup du role ULB du servers",
            description=f"Role **ULB** : {role_ulb.mention}",
            color=disnake.Color.green(),
        ).set_footer(text='Utilise "/role_update" pour mettre à jour les roles des membres de ce serveur.')

        # Add warning if @everyone or @ulb has the permisions to edit their own nickname
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
        # Add warning if the role order does not allow the bot to edit the nickname of @ulb
        if inter.me.top_role <= role_ulb:
            embed.add_field(
                name="⚠️",
                value=f"Le role {inter.me.mention} doit être au dessus de {role_ulb.mention} pour pouvoir changer leur pseudo, ce qui n'est pas le cas actuellement !",
            )

        await inter.edit_original_message(embed=embed)

    @commands.slash_command(
        name="update",
        description="Mettre à jour les roles des members de ce serveur (uniquement ajoute les nouveaux membres).",
        default_member_permissions=disnake.Permissions.all(),
    )
    async def update(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.wait_data()

        ulb_role = Database.ulb_guilds.get(inter.guild, None)

        # Check if ulb role is set
        if not ulb_role:
            await inter.edit_original_message(
                embed=disnake.Embed(
                    description="""Le role **ULB** de ce serveur n'est pas encore setup ! Utilise **"/role setup"** pour le sélectionner.""",
                    color=disnake.Color.orange(),
                )
            )

        # Update the guild
        await utils.update_guild(inter.guild, role=ulb_role)
        await inter.edit_original_message(
            embed=disnake.Embed(description="Mise à jour finie !", color=disnake.Color.green())
        )

    # FIXME: Event is not triggered ?
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        await self.wait_data()

        ulb_role = Database.ulb_guilds.get(member.guild, None)
        # if ulb_role is None, this mean that the guild is not set
        if not ulb_role:
            return

        name = Database.ulb_users.get(member, None)
        # If name is None, this mean that the member is not registered yet
        if not name:
            await member.send(
                embed=disnake.Embed(
                    title=f"__Bienvenu sur le server **{member.guild.name}**__",
                    description="""Ce serveur est reservé aux membre de l'ULB. Pour acceder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande **"/email"**.""",
                    color=disnake.Color.teal(),
                ).set_thumbnail(url=self.bot.BEP_image)
            )
        else:
            await utils.update_member(member)

    # FIXME: Event is not triggered ?
    @commands.Cog.listener("on_guild_join")
    async def on_member_join(self, guild: disnake.Guild):
        # Autodetect ULB role for guild that follow the ULB guild template
        if self.ulb_guil_template_url and self.ulb_guil_template_url in [t.code for t in await guild.templates()]:
            for role in guild.roles:
                if role.name == "ULB":
                    Database.set_guild(guild, role)
                    logging.info(
                        f"[Cog:Ulb] New guild following ULB template joined. Role {role.name}:{role.id} automatically set as ULB role."
                    )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
