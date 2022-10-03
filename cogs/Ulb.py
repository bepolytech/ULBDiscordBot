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

    async def wait_setup(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Async sleep until GoogleSheet is loaded and RegistrationForm is set"""
        if await utils.wait_data(inter, 15):
            if not Registration.set:
                logging.trace("[Cog:Ulb]  Waiting for registrationForm to be set...")
                max_time = 10
                current_time = 0
                while not Registration.set and current_time < max_time:
                    await asyncio.sleep(1)
                    current_time += 1
                if not Registration.set:
                    await inter.edit_original_response(
                        embed=disnake.Embed(
                            title="Commande temporairement inaccessible",
                            description="Veuillez réessayer dans quelques instants.",
                            color=disnake.Color.orange(),
                        )
                    )
                return False
        return True

    @commands.slash_command(name="ulb", description="Vérifier son adresse mail ULB.")
    async def ulb(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not (await self.wait_setup(inter)):
            return

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
        await inter.response.defer(ephemeral=True)

        if not (await utils.wait_data(inter, 15)):
            return

        if role_ulb == inter.guild.default_role:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="Setup du role ULB du servers",
                    description=f"Le role {role_ulb.mention} ne peux pas être utilisé comme role **ULB** !.",
                    color=disnake.Color.red(),
                )
            )
            return

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
            embed.add_field(
                name="⚠️",
                value=role_ulb.mention
                + " a la permission de changer leur propre pseudo.\nRetirez cette permission si vous voulez que les membres soit obligés de garder leur vrai nom.",
            ).set_footer(
                text="""Vous pouvez utiliser cette commande avec le même role ou "/info" pour vérifier l'état des permissions."""
            )

        await inter.edit_original_message(embed=embed)

        await utils.update_guild(inter.guild, role=role_ulb)

    @commands.slash_command(
        name="info",
        description="Voir les settings pour ce serveurs",
        default_member_permissions=disnake.Permissions.all(),
        dm_permission=False,
    )
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not (await self.wait_setup(inter)):
            return

        guilddata = Database.ulb_guilds.get(inter.guild, None)

        if guilddata == None:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="Info du serveur",
                    description="Ce serveur n'est pas encore configurer.\nUtilisez **/setup** pour commencer.",
                    color=disnake.Color.orange(),
                )
            )

        embed = disnake.Embed(
            title="Info du serveur",
            description=f"ULB role : {guilddata.role.mention}\nRenommer les membres : **{'oui' if guilddata.rename else 'non'}**",
            color=disnake.Color.green(),
        )

        if guilddata.rename and guilddata.role.permissions.change_nickname:
            embed.add_field(
                name="⚠️",
                value=guilddata.role.mention
                + " a la permission de changer leur propre pseudo.\nRetirez cette permission si vous voulez que les membres soit obligés de garder leur vrai nom.",
            )
        else:
            embed.add_field(
                name="✅",
                value="Pas de conflit de permission",
            )
        await inter.edit_original_response(embed=embed)

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        if not (await utils.wait_data()):
            return
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
        if not (await utils.wait_data()):
            return
        guild_data = Database.ulb_guilds.get(after.guild, None)
        if (
            guild_data
            and guild_data.rename
            and after == guild_data.role
            and before.permissions.change_nickname == False
            and after.permissions.change_nickname == True
        ):
            logging.trace(
                f"[Cog:Ulb] [Guild {after.guild.name}:{after.guild.id}] [Role {after.name}:{after.id}] Nickname permission conflict detected. Sending message to editer user..."
            )
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
                    logging.info(
                        f"[Cog:Ulb] [Guild {after.guild.name}:{after.guild.id}] [Role {after.name}:{after.id}] Nickname permission conflict: Warning sent to {audit.user.name}:{audit.user.id}."
                    )
                    return
            logging.warning(
                f"[Cog:Ulb] [Guild {after.guild.name}:{after.guild.id}] [Role {after.name}:{after.id}] Nickname permission conflict: Not able to found editer user from auditlog."
            )

    @commands.Cog.listener("on_guild_role_delete")
    async def on_guild_role_delete(self, role: disnake.Role):
        if not (await utils.wait_data()):
            return
        guild_data = Database.ulb_guilds.get(role.guild, None)
        if guild_data:
            logging.trace(
                f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}] Role deleted: Remonving entry from database..."
            )
            Database.delete_guild(role.guild)
            logging.trace(
                f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}] Role deleted Entry removed from database. Sending message to editer user..."
            )
            async for audit in role.guild.audit_logs(action=disnake.AuditLogAction.role_delete, limit=10):
                if audit.target == role:
                    await audit.user.send(
                        embed=disnake.Embed(
                            title="Supression du role **ULB**.",
                            description=f"""Vous avez supprimé le role **@{role.name}** du serveur **{role.guild.name}**.\nCe role était paramètré comme le role **ULB** qui est attribué automatiquement aux membres ayant vérifiés leur email **ULB**.\nPour choisir un nouveau role **ULB**, vous pouvez utilisez **"/setup"** dans le serveur.""",
                            color=disnake.Colour.red(),
                        )
                    )
                    logging.info(
                        f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}] Role deleted: warning sent to {audit.user.name}:{audit.user.id}"
                    )
                    return
            logging.warning(
                f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}]  Role deleted: Not able to found editer user from auditlog."
            )

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove(self, guild: disnake.Guild):
        if not (await utils.wait_data()):
            return

        if guild in Database.ulb_guilds.keys():
            logging.trace(f"[Cog:Ulb] [Guild {guild.name}:{guild.id}] Guild removed: Deleting entey from database...")
            await Database.delete_guild(guild)
            logging.info(f"[Cog:Ulb] [Guild {guild.name}:{guild.id}] Guild removed: Entry deleted from database.")

    @commands.Cog.listener("on_resumed")
    async def on_resumed(self):
        await utils.update_all_guilds()


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
