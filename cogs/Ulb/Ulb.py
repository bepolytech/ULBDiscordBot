# -*- coding: utf-8 -*-
import logging
import os
import pickle
from typing import Dict
from typing import List

import disnake
from disnake import ApplicationCommandInteraction
from disnake.client import HTTPException
from disnake.ext import commands

from .modals import *
from .ULBUser import ULBUser
from bot import Bot
from cogs.Ulb.registrationForm import RegistrationForm


class Ulb(commands.Cog):

    data_path: str = "cogs/Ulb/data.json"

    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot
        self.ulb_guilds: Dict[disnake.Guild, disnake.Role] = {}
        self.ulb_users: Dict[disnake.User, ULBUser] = {}
        self.pending_registration_users: List[disnake.User] = []
        self.pending_registration_emails: List[str] = []
        self.data_loaded = False
        # self.clear_data()

    def clear_data(self):
        with open(self.data_path, "wb") as json_file:
            pickle.dump({"ulb_guilds": {}, "ulb_users": {}}, json_file)

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        with open(self.data_path, "rb") as json_file:
            logging.debug("Loading data...")
            data: Dict[str, dict] = pickle.load(json_file)

        ulb_guilds_data: Dict[str, int] = data.get("ulb_guilds")
        for guild_id, role_id in ulb_guilds_data.items():
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                role = guild.get_role(role_id)
                if role:
                    self.ulb_guilds.setdefault(guild, role)
                    logging.debug(f"Role {role.name}:{role.id} loaded from guild {guild.name}:{guild.id} ")
                else:
                    logging.warning(f"Unable to find role from {role_id=} in guild {guild.name}:{guild.id}.")
            else:
                logging.warning(f"Unable to find guild from {guild_id=}.")

        ulb_users_data: Dict[str, Dict[str, str]] = data.get("ulb_users")
        for user_id, user_data in ulb_users_data.items():
            user = self.bot.get_user(int(user_id))
            if user:
                self.ulb_users.setdefault(user, ULBUser(user_data.get("name"), user_data.get("email")))
                logging.debug(
                    f"User {user.name}:{user.id} loaded with name={user_data.get('name')} and email={user_data.get('email')}"
                )
            else:
                logging.warning(f"Unable to find user from {user_id=}.")

        self.data_loaded = True
        logging.info("ULB data loaded")

    def save_data(self) -> None:
        """Save the tag_role_map to the json file"""
        data = {}
        data.setdefault("ulb_guilds", {str(guild.id): role.id for guild, role in self.ulb_guilds.items()})
        data.setdefault("ulb_users", {str(user.id): dict(user_data) for user, user_data in self.ulb_users.items()})

        with open(self.data_path, "wb") as json_file:
            pickle.dump(data, json_file)

    async def wait_data(self) -> None:
        while self.data_loaded == False:
            await asyncio.sleep(1)

    @commands.slash_command(name="email", description="Vérifier son adresse mail ULB.")
    async def email(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not self.data_loaded:
            logging.debug("Waiting for data to be loaded.")
            await self.wait_data()
        form = RegistrationForm(inter.user, self)
        await form.start(inter)

    @commands.slash_command(name="role", default_member_permissions=disnake.Permissions.all())
    async def roles(self, inter: ApplicationCommandInteraction):
        pass

    @roles.sub_command(name="setup", description="Sélectionner le role ULB de ce serveur.")
    async def roles_setup(
        self, inter: ApplicationCommandInteraction, role_ulb: disnake.Role = commands.Param(description='Le role "ULB"')
    ):
        await inter.response.defer(ephemeral=True)
        if not self.data_loaded:
            logging.debug("Waiting for data to be loaded.")
            await self.wait_data()

        self.ulb_guilds[inter.guild] = role_ulb
        self.save_data()

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

        await inter.edit_original_message(embed=embed)

    @roles.sub_command(
        name="update",
        description="Mettre à jour les roles des members de ce serveur (uniquement ajoute les nouveaux membres).",
    )
    async def roles_update(self, inter: ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not self.data_loaded:
            logging.debug("Waiting for data to be loaded.")
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
                                f'Error adding ulb role "{ulb_role.name}:{ulb_role.id}" from guild "{inter.guild.name}:{inter.guild.id}" to ulb user "{member.name}:{member.id}": {ex}'
                            )
                    if member.display_name != ulb_user.name:
                        try:
                            await member.edit(nick=f"{ulb_user.name}")
                        except HTTPException as ex:
                            logging.warning(
                                f'Error editing user "{member.name}:{member.id}" nick to "{ulb_user.name}": {ex}'
                            )
            await inter.edit_original_message(
                embed=disnake.Embed(description="Mise à jour finie !", color=disnake.Color.green())
            )
        else:
            logging.error(
                f"Unable to find ulb role from id={self.ulb_guilds.get(inter.guild)} for guild {inter.guild.name}:{inter.guild.id}."
            )
            await inter.edit_original_message(
                embed=disnake.Embed(
                    description=""""Impossible de trouver le role ULB.\nSi celui-ci a été supprimé, il est nécessaire d'en sélectionner un autre avec **"/role setup"**.""",
                    color=disnake.Color.orange(),
                )
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        if not self.data_loaded:
            logging.debug("Waiting for data to be loaded.")
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
                        f'Error adding ulb role "{self.ulb_guilds.get(member.guild).name}:{self.ulb_guilds.get(member.guild).id}" from guild "{member.guild.name}:{member.guild.id}" to ulb user "{member.name}:{member.id}": {ex}'
                    )
                try:
                    await member.edit(nick=f"{self.ulb_users.get(member).name}")
                except HTTPException as ex:
                    logging.warning(
                        f'Error editing user "{member.name}:{member.id}" nick to "{self.ulb_users.get(member).name}": {ex}'
                    )

    @commands.Cog.listener("on_guild_join")
    async def on_member_join(self, guild: disnake.Guild):
        # Autodetect ULB role for guild that follow the ULB guild template
        if os.getenv("GUILD_TEMPLATE_CODE") in [t.code for t in await guild.templates()]:
            for role in guild.roles:
                if role.name == "ULB":
                    self.ulb_guilds[guild] = role
                    logging.info(
                        f"New guild following ULB template joined. Role {role.name}:{role.id} automatically set as ULB role."
                    )


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
