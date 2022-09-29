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
        Registration.setup(self)
        logging.info("[Cog:Ulb] Ready !")
        logging.info("[Cog:Ulb] Checking all guilds...")
        await asyncio.gather(*[utils.update_guild(guild, role=role) for guild, role in Database.ulb_guilds.items()])
        logging.info("[Cog:Ulb] All guilds checked !")

    async def wait_data(self) -> None:
        """Async sleep until GoogleSheet is loaded"""
        if not Database.loaded:
            logging.trace("[Cog:Ulb] Waiting for data to be load from google sheet...")
            await asyncio.sleep(1)
        while not Database.loaded:
            await asyncio.sleep(1)

    async def wait_setup(self) -> None:
        """Async sleep until GoogleSheet is loaded and RegistrationForm is set"""
        if not Database.loaded:
            await self.wait_data()
        if not Registration.set:
            logging.trace("[Cog:Ulb]  Waiting for registrationForm to be set...")
            await asyncio.sleep(1)
        while not Registration.set:
            await asyncio.sleep(1)

    @commands.slash_command(name="email", description="Vérifier son adresse mail ULB.")
    async def email(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.wait_setup()

        await Registration.new(inter)

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
            description=f"""> Role **ULB** : {role_ulb.mention}.\n\nLes nouveaux membres seront automatiquement ajoutés à {role_ulb.mention} et renommer avec leur vrai nom une fois qu'ils auront vérifiés leur adresse email ULB.""",
            color=disnake.Color.green(),
        ).set_thumbnail(url=Bot.ULB_image)

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
                + " ont la permission de changer leur propre pseudo.\nRetirez cette permission si vous voulez que les membres soit obligés de garder leur vrai nom.",
            ).set_footer(
                text="Vous pouvez réutiliser cette commande avec le même role pour vérifier l'état des permissions."
            )
        # Add warning if the role order does not allow the bot to edit the nickname of @ulb
        if inter.me.top_role <= role_ulb:
            embed.add_field(
                name="⚠️",
                value=f"Le role {inter.me.mention} doit être au dessus de {role_ulb.mention} pour pouvoir changer leur pseudo, ce qui n'est pas le cas actuellement !",
            ).set_footer(
                text="Vous pouvez réutiliser cette commande avec le même role pour vérifier l'état des permissions."
            )

        await inter.edit_original_message(embed=embed)

        await utils.update_guild(inter.guild, role=role_ulb)

    # FIXME: Event is not triggered ?
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        await self.wait_data()
        logging.trace(f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] user joined")

        ulb_role = Database.ulb_guilds.get(member.guild, None)
        # if ulb_role is None, this mean that the guild is not set
        if not ulb_role:
            logging.trace(f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] Guild is not set. Ending event")
            return

        name = Database.ulb_users.get(member, None)
        # If name is None, this mean that the member is not registered yet
        if not name:
            logging.trace(
                f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] Member not registered yet. Sending message."
            )
            await member.send(
                embed=disnake.Embed(
                    title=f"__Bienvenu sur le server **{member.guild.name}**__",
                    description="""Ce serveur est reservé aux membre de l'ULB. Pour acceder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande **"/email"**.""",
                    color=disnake.Color.teal(),
                ).set_thumbnail(url=self.bot.ULB_image)
            )
        else:
            logging.trace(
                f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] Member already registered. Updating member."
            )
            await utils.update_member(member)

    # FIXME: Event is not triggered ?
    @commands.Cog.listener("on_guild_join")
    async def on_member_join(self, guild: disnake.Guild):

        logging.trace(f"[Cog:Ulb] [Guild:{guild.id}] Bot joined a new guild")
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
