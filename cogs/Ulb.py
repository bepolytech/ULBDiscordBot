# -*- coding: utf-8 -*-
import asyncio
import logging

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from bot import Bot
from classes import *
from classes.feedback import FeedbackModal
from classes.feedback import FeedbackType


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

    @commands.slash_command(name="ulb", description="Gérer son adresse email ULB.")
    async def ulb(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not (await self.wait_setup(inter)):
            return
        if inter.author in Database.ulb_users.keys():
            await Unregister.new(inter)
        else:
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
        role_ulb: disnake.Role = commands.Param(description='Le rôle "**ULB**" à donner aux membres vérifiés.'),
        rename: str = commands.Param(
            description="Est-ce que les membres doivent être renommer avec leur vrai nom.",
            default="Oui",
            choices=["Non", "Oui"],
        ),
    ):
        await inter.response.defer(ephemeral=True)

        if not (await utils.wait_data(inter, 15)):
            return

        if inter.guild.me.top_role.permissions.manage_roles != True:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="Setup du rôle ULB du serveur",
                    description=f"J'ai besoin d'avoir la permissions d'éditer les rôles pour pouvoir ajouter les membres vérifiés à {role_ulb.mention}.\nChangez mes permissions et réessayez.",
                    color=disnake.Colour.red(),
                )
            )
            return

        if rename == True and inter.guild.me.top_role.permissions.manage_nicknames != True:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="Setup du rôle ULB du serveur",
                    description=f"J'ai besoin d'avoir la permissions d'éditer les pseudos des membres pour pouvoir les renommer avec leur vrai nom.\nChangez mes permissions et réessayez.",
                    color=disnake.Colour.red(),
                )
            )
            return

        if role_ulb == inter.guild.default_role:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="Setup du rôle ULB du serveur",
                    description=f"Le rôle {role_ulb.mention} ne peux pas être utilisé comme role '**ULB**' car c'est le rôle par défaut.",
                    color=disnake.Color.red(),
                )
            )
            return

        rename = rename == "Oui"  # Convert from str to bool

        Database.set_guild(inter.guild, role_ulb, rename)
        embed = disnake.Embed(
            title="Setup du rôle ULB du serveur",
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
                inline=False,
            )

        if rename and inter.me.top_role <= role_ulb:
            embed.add_field(
                name="⚠️",
                value=f"Le rôle {inter.me.top_role.mention} doit être au dessus de {role_ulb.mention} pour pouvoir update le nom des utilisateur.rice.s enregistré.e.s.",
                inline=False,
            )
        if embed.fields != []:
            embed.color = disnake.Color.orange()
            embed.set_footer(text="""Vous pouvez utiliser "/info" pour vérifier l'état des permissions.""")

        await inter.edit_original_message(embed=embed)

        await utils.update_guild(inter.guild, role=role_ulb)

    @commands.slash_command(
        name="info",
        description="Voir les settings pour ce serveur",
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
                    description="Ce serveur n'est pas encore configuré.\nUtilisez **/setup** pour commencer.",
                    color=disnake.Color.orange(),
                )
            )
            return

        n_registered = len(guilddata.role.members)
        percent = int(n_registered / inter.guild.member_count * 100)

        embed = disnake.Embed(
            title="Info du serveur",
            description=f"ULB role : {guilddata.role.mention}\nNombre de membre vérifié : **{n_registered}** *({percent}%)*\nRenommer les membres : **{'oui' if guilddata.rename else 'non'}**",
            color=disnake.Color.green(),
        )

        if inter.guild.me.top_role.permissions.manage_roles != True:
            embed.add_field(
                name="❌", value="je n'ai pas la permissions de changer les rôles des membres.", inline=False
            )

        if guilddata.rename and inter.guild.me.top_role.permissions.manage_nicknames != True:
            embed.add_field(
                name="❌", value="je n'ai pas la permissions de changer le pseudo des membres vérifiés.", inline=False
            )

        if guilddata.rename and guilddata.role.permissions.change_nickname:
            embed.add_field(
                name="⚠️",
                value=guilddata.role.mention
                + " a la permission de changer leur propre pseudo.\nRetirez cette permission si vous voulez que les membres soit obligés de garder leur vrai nom.",
                inline=False,
            )

        if guilddata.rename and inter.me.top_role <= guilddata.role:
            embed.add_field(
                name="⚠️",
                value=f"Le rôle {inter.me.top_role.mention} doit être au dessus de {guilddata.role.mention} pour pouvoir update le nom des utilisateurs enregistrés.",
                inline=False,
            )

        if embed.fields == []:
            embed.add_field(
                name="✅",
                value="Aucun conflit de permission",
            )
        else:
            embed.color = disnake.Colour.orange()
        await inter.edit_original_response(embed=embed)

    @commands.slash_command(name="feedback", description="Envoyer un feedback.")
    async def feedback(
        self,
        inter: disnake.ApplicationCommandInteraction,
        type: str = commands.Param(description="type de feedback", choices=[FeedbackType.issu, FeedbackType.improve]),
    ):
        logging.trace(f"[Feedback] Starting {type} feedback by {inter.user} from {inter.guild}")
        await inter.response.send_modal(modal=FeedbackModal(self.bot, type))

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
                    title=f"Bienvenue sur le serveur __**{member.guild.name}**__",
                    description="""Ce serveur est limité aux membre de l'**ULB**.\nPour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande **"/ulb"**.""",
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
                            title="Modification des permissions du rôle **ULB**.",
                            description=f"Vous avez autorisé le rôle **@{after.name}** du serveur **{after.guild.name}** à modifier son propre pseudo.\nCe rôle est paramètré comme le rôle **ULB** qui est attribué automatiquement aux membres ayant vérifiés leur email **ULB** et ce serveur est paramètré pour que ces membres soient renommés avec leur vrai nom.\nSi vous gardez les permissions et paramètres actuels, les nouveaux membres vérifiés seront toujours renommés automatiquement mais pourront changer leur pseudo ensuite.\nSi vous désirez changer mes paramètres pour ce serveur, vous pouvez utiliser **/setup** dans le serveur.",
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
                            title="Supression du rôle **ULB**.",
                            description=f"""Vous avez supprimé le rôle **@{role.name}** du serveur **{role.guild.name}**.\nCe rôle était paramétré comme le rôle **ULB** qui était attribué automatiquement aux membres ayant vérifiés leur email **ULB**.\nCette fonctionnalité a été retirée et vous devrez la re-configurer en utilisant **"/setup"** dans le serveur.""",
                            color=disnake.Colour.red(),
                        )
                    )
                    logging.info(
                        f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}] Role deleted: warning sent to {audit.user.name}:{audit.user.id}"
                    )
                    return
            logging.warning(
                f"[Cog:Ulb] [Guild {role.guild.name}:{role.guild.id}] [Role {role.name}:{role.id}] Role deleted: Not able to found editer user from auditlog."
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

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join(self, guild: disnake.Guild):
        async for audit in guild.audit_logs(action=disnake.AuditLogAction.bot_add):
            if audit.target == guild.me:
                embed = disnake.Embed(
                    title="Nouveau serveur",
                    description=f"Vous venez de m'inviter dans le serveur {guild.name}, mais je n'ai pas les autorisations suffisantes pour être utilisé.\nDonnez moi les autorisations listées ci-dessous et changez la position de mon rôle ({guild.me.top_role.mention}) dans la liste des rôles du serveur pour que je sois juste en dessous des modérateurs.\nPour plus d'informations, consultez ma page [Github](https://github.com/bepolytech/ULBDiscordBot).",
                    color=disnake.Colour.red(),
                )
                perms = guild.me.top_role.permissions
                if perms.manage_roles != True:
                    embed.add_field(
                        name="❌",
                        value="Je n'ai pas la permissions de **changer les rôles**, ce dont j'ai besoin pour ajouter les membres vérifiés au rôle correspondant.",
                        inline=False,
                    )
                if perms.manage_nicknames != True:
                    embed.add_field(
                        name="⚠️",
                        value="Je n'ai pas la permissions de changer le pseudo des membres de ce serveur, ce qui veut dire que vous ne pourrez pas forcer les membres vérifiés à utiliser leur vrai nom comme pseudo.",
                        inline=False,
                    )
                if embed.fields != []:
                    await audit.user.send(embed=embed)
                    await guild.leave()
                else:
                    await audit.user.send(
                        embed=disnake.Embed(
                            title="Nouveau serveur",
                            description=f"Vous venez de m'inviter dans le serveur {guild.name}.\nChangez la position de mon rôle ({guild.me.top_role.mention}) dans la liste des rôles du serveur pour que que je sois juste en dessous des modérateurs.\nUtilisez ensuite la commande **/setup** dans le serveur pour me configurer.\nPour plus d'informations, consultez ma page [Github](https://github.com/bepolytech/ULBDiscordBot).",
                            color=disnake.Colour.green(),
                        )
                    )
                return


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
