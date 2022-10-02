# -*- coding: utf-8 -*-
import asyncio
import logging

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from bot import Bot
from classes import *


class Ulb(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        Database.load(self.bot)
        Registration.setup(self)
        logging.info("[Cog:Ulb] Ready !")
        await utils.update_all_guilds()

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

    @commands.slash_command(name="ulb", description="Vérifier son adresse mail ULB.")
    async def ulb(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        await self.wait_setup()

        await Registration.new(inter)

    @commands.slash_command(
        name="setup",
        description="Sélectionner le role ULB de ce serveur.",
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def setup(
        self,
        inter: ApplicationCommandInteraction,
        role_ulb: disnake.Role = commands.Param(description='Le role "ULB" à donner aux membres vérifiés.'),
        rename: str = commands.Param(
            description="Est-ce que les membres doivent être renommer avec leur vrai nom.",
            default="Oui",
            choices=["Non", "Oui"],
        ),
    ):

        if role_ulb == inter.guild.default_role:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title="Setup du role ULB du servers",
                    description=f"Le role {role_ulb.mention} ne peux pas être utilisé comme role **ULB** !.",
                    color=disnake.Color.red(),
                )
            )
            return

        await inter.response.defer(ephemeral=True)
        await self.wait_data()

        rename = rename == "Oui"  # Convert from str to bool

        Database.set_guild(inter.guild, role_ulb, rename)
        embed = disnake.Embed(
            title="Setup du role ULB du servers",
            description=f"""✅ Setup confirmé !\n\n> Les nouveaux membres seront automatiquement ajoutés à {role_ulb.mention}"""
            + (" et renommés avec leur vrai nom " if rename else " ")
            + "une fois qu'ils auront vérifiés leur adresse email **ULB**.",
            color=disnake.Color.green(),
        ).set_thumbnail(url=Bot.ULB_image)

        if rename and role_ulb.permissions.change_nickname:
            try:
                await role_ulb.edit(permissions=disnake.Permissions(change_nickname=False, manage_nicknames=False))
            except disnake.Forbidden:
                embed.add_field(
                    name="⚠️",
                    value=role_ulb.mention
                    + " ont la permission de changer leur propre pseudo et je ne peux pas modifier celle-ci.\nRetirez cette permission si vous voulez que les membres soit obligés de garder leur vrai nom.",
                ).set_footer(
                    text="Vous pouvez réutiliser cette commande avec le même role pour vérifier l'état des permissions."
                )
            else:
                embed.add_field(
                    name="⚠️",
                    value=role_ulb.mention
                    + " avait la permission de changer leur propre pseudo.\nJ'ai retiré cette permissions pour forcer les membres à garder leur vrai nom.",
                ).set_footer(
                    text="Vous pouvez réutiliser cette commande avec le même role pour vérifier l'état des permissions."
                )

        await inter.edit_original_message(embed=embed)

        await utils.update_guild(inter.guild, role=role_ulb)

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        await self.wait_data()
        logging.trace(f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] user joined")

        guild_data = Database.ulb_guilds.get(member.guild, None)
        # if ulb_role is None, this mean that the guild is not set
        if guild_data == None:
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
                    title=f"Bienvenu sur le server __**{member.guild.name}**__",
                    description="""Ce serveur est reservé aux membre de l'ULB.\nPour acceder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande **"/ulb"**.""",
                    color=disnake.Color.teal(),
                ).set_thumbnail(url=self.bot.ULB_image)
            )
        else:
            logging.trace(
                f"[Cog:Ulb] [Guild:{member.guild.id}] [User:{member.id}] Member already registered. Updating member."
            )
            await utils.update_member(member, role=guild_data.role, rename=guild_data.rename)

    @commands.Cog.listener("on_guild_role_update")
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
        guild_data = Database.ulb_guilds.get(after.guild, None)
        if (
            guild_data
            and guild_data.rename
            and after == guild_data.role
            and before.permissions.change_nickname == False
            and after.permissions.change_nickname == True
        ):
            async for audit in after.guild.audit_logs(action=disnake.AuditLogAction.role_update, limit=10):
                if (
                    audit.target == after
                    and audit.before.permissions.change_nickname == False
                    and audit.after.permissions.change_nickname == True
                ):
                    await audit.user.send(
                        embed=disnake.Embed(
                            title="Modification des permissions du role **ULB**.",
                            description=f"Vous avez autorisé le role **@{after.name}** du serveur **{after.guild.name}** à modifier son propre pseudo.\nCe role est paramètré comme le role **ULB** qui est attribué automatiquement aux membres ayant vérifiés leur email **ULB** et ce serveur est paramètré pour ces membres soient renommé avec leur vrai nom.\nSi vous gardez les permissions et paramètres actuels, les nouveaux membres vérifiés seront toujours renommés automatiquement mais pourront changer leur pseudo ensuite.\nSi vous désirez changer mes paramètres pour ce serveur, vous pouvez utiliser **/setup** dans le serveur.",
                            color=disnake.Colour.orange(),
                        )
                    )
                    return

    @commands.Cog.listener("on_guild_role_delete")
    async def on_guild_role_delete(self, role: disnake.Role):
        guild_data = Database.ulb_guilds.get(role.guild, None)
        if guild_data:
            Database.delete_guild(role.guild)
            async for audit in role.guild.audit_logs(action=disnake.AuditLogAction.role_delete, limit=10):
                if audit.target == role:
                    await audit.user.send(
                        embed=disnake.Embed(
                            title="Supression du role **ULB**.",
                            description=f"""Vous avez supprimé le role **@{role.name}** du serveur **{role.guild.name}**.\nCe role était paramètré comme le role **ULB** qui est attribué automatiquement aux membres ayant vérifiés leur email **ULB**.\nPour choisir un nouveau role **ULB**, vous pouvez utilisez **"/setup"** dans le serveur.""",
                            color=disnake.Colour.red(),
                        )
                    )
                    return

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove(self, guild: disnake.Guild):
        await Database.delete_guild(guild)

    @commands.Cog.listener("on_resumed")
    async def on_resumed(self):
        await utils.update_all_guilds()


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
