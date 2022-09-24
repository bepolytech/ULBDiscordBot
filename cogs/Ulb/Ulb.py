# -*- coding: utf-8 -*-
import logging
import os
import pickle
import secrets
from typing import Dict
from typing import List
from typing import Union

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from .emailManager import EmailManager
from .modals import *
from bot import Bot


class ULBGuild:
    def __init__(
        self, *, role_ulb: disnake.Role = None, role_bep: disnake.Role = None, role_bep_it: disnake.Role = None
    ):
        self.role_ulb: disnake.Role = role_ulb
        self.role_bep: disnake.Role = role_bep
        self.role_bep_it: disnake.Role = role_bep_it

    def __iter__(self):
        yield "role_ulb", self.role_ulb.id if self.role_ulb else None
        yield "role_bep", self.role_bep.id if self.role_ulb else None
        yield "role_bep_it", self.role_bep_it.id if self.role_ulb else None

    @staticmethod
    def load(guild: disnake.Guild, data: Dict[str, int]) -> "ULBGuild":
        return ULBGuild(
            role_ulb=guild.get_role(data.get("role_ulb")),
            role_bep=guild.get_role(data.get("role_bep")),
            role_bep_it=guild.get_role(data.get("role_bep_it")),
        )


class ULBUser:
    def __init__(self, name: str, email: str, *, bep: bool = False, bep_it: bool = False):
        self.name: str = name
        self.email: str = email
        self.bep: bool = bep
        self.bep_it: bool = bep_it

    def __iter__(self):
        yield "name", self.name
        yield "email", self.email
        yield "bep", self.bep
        yield "bep_it", self.bep_it

    @staticmethod
    def load(data: Dict[str, Union[str, bool]]) -> "ULBUser":
        return ULBUser(
            name=str(data.get("name")),
            email=str(data.get("email")),
            bep=bool(data.get("bep")),
            bep_it=bool(data.get("bep_it")),
        )


class Ulb(commands.Cog):

    data_path: str = "cogs/Ulb/data.json"

    token_size: int = 10
    token_validity_time: int = 10 * 60  # In sec

    valid_email_domaines = ("ulb.be", "ulb.ac.be")

    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot
        self.ulb_guilds: Dict[disnake.Guild, ULBGuild] = {}
        self.ulb_users: Dict[disnake.User, ULBUser] = {}
        self.emailManager = EmailManager()
        self.pending_registration_emails: List[str] = []
        # self.clear_data()

    def clear_data(self):
        with open(self.data_path, "wb") as json_file:
            pickle.dump({"ulb_guilds": {}, "ulb_users": {}}, json_file)

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        with open(self.data_path, "rb") as json_file:
            data: Dict[str, dict] = pickle.load(json_file)

        for guild in self.bot.guilds:
            if str(guild.id) in data.get("ulb_guilds").keys():
                self.ulb_guilds.setdefault(guild, ULBGuild.load(guild, data.get("ulb_guilds").get(str(guild.id))))

        for user in self.bot.users:
            if str(user.id) in data.get("ulb_users").keys():
                self.ulb_users.setdefault(user, ULBUser.load(data.get("ulb_users").get(str(user.id))))
        logging.info("ULB data loaded")

    def save_data(self) -> None:
        """Save the tag_role_map to the json file"""
        data = {}
        data.setdefault(
            "ulb_guilds", {str(guild.id): dict(guild_data) for guild, guild_data in self.ulb_guilds.items()}
        )
        data.setdefault("ulb_users", {str(user.id): dict(user_data) for user, user_data in self.ulb_users.items()})

        with open(self.data_path, "wb") as json_file:
            pickle.dump(data, json_file)

    async def register_user(self, *, user: disnake.User, name: str, email: str):
        """Add a user with his verified email address to the database

        Parameters
        ----------
        user : `disnake.User`
            The user to add
        email : `str`
            The verified email address
        """
        self.ulb_users.setdefault(user, ULBUser(name, email))
        self.save_data()

        for guild in self.ulb_guilds:
            member = guild.get_member(user.id)
            if member:
                await member.add_roles(self.ulb_guilds.get(guild).role_ulb)

    def check_email_validity(self, email: str) -> bool:
        """Check the validity of an ulb addresse mail format.
        Does not check if the address mail do actually exist!

        Parameters
        ----------
        mail : `str`
            The email address

        Returns
        -------
        `bool`
            `True``if the address mail format is valid. `False` otherwise.
        """
        if not email:  # mail could be empty
            return False
        splited_mail: List[str] = email.split("@")
        if len(splited_mail) != 2:  # not exactly one "@" on the address
            return False
        if splited_mail[1] not in self.valid_email_domaines:  # Not a ulb addresse mail
            return False
        return True

    def check_email_unicity(self, email: str) -> bool:
        """Check if the email is already used for a registered user

        Parameters
        ----------
        email : `str`
            The email address to check

        Returns
        -------
        bool
            `True` is the email address is available (no current registered user is associated with it). `False` otherwise
        """
        if email in self.pending_registration_emails:
            return False
        self.pending_registration_emails.append(email)
        for user_data in self.ulb_users.values():
            if user_data.email == email:
                return False
        return True

    def send_token_mail(self, email: str) -> str:
        """Generate and send a token to the given email address

        Parameters
        ----------
        mail : `str`
            The email address to which send the token

        Returns
        -------
        `str`
            The token generated
        """
        token: str = secrets.token_hex(self.token_size)[: self.token_size]
        self.emailManager.sendToken(email, token)
        return token

    @commands.slash_command(name="email", description="Vérifier son adresse mail ULB.")
    async def email(self, inter: ApplicationCommandInteraction):
        if inter.user in self.ulb_users.keys():
            await inter.response.send_message(
                embed=disnake.Embed(
                    title=title,
                    description=f"Tu as déjà associé l'addresse mail suivante : **{self.ulb_users.get(inter.user).email}**\nSi ce n'est pas ton addresse mail ULB, contact un membre de {self.ulb_guilds.get(inter.guild).role_bep_it.mention if self.ulb_guilds.get(inter.guild) else '**BEP IT**'}.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image),
                ephemeral=True,
            )
        else:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title=title,
                    description="Ce serveur est réservé aux étudiants de la faculté polytechnique de l'ULB.\nPour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB**.",
                    color=disnake.Color.teal(),
                ).set_thumbnail(Bot.BEP_image),
                view=RegisterView(self),
                ephemeral=True,
            )

    @commands.slash_command(name="roles", default_member_permissions=disnake.Permissions.all())
    async def roles(self, inter: ApplicationCommandInteraction):
        pass

    @roles.sub_command(name="setup", description="Sélectionner les roles ULB, BEP et BEP IT de ce serveur.")
    async def roles_setup(
        self,
        inter: ApplicationCommandInteraction,
        role_ulb: disnake.Role = commands.Param(description='Le role "ULB"', default=None),
        role_bep: disnake.Role = commands.Param(description='Le role "BEP"', default=None),
        role_bep_it: disnake.Role = commands.Param(description='Le role "BEP IT"', default=None),
    ):
        if inter.guild in self.ulb_guilds.keys():
            guildData = self.ulb_guilds[inter.guild]
            if role_ulb:
                guildData.role_ulb = role_ulb
            if role_bep:
                guildData.role_bep = role_bep
            if role_bep_it:
                guildData.role_bep_it = role_bep_it
        else:
            self.ulb_guilds[inter.guild] = ULBGuild(role_ulb=role_ulb, role_bep=role_bep, role_bep_it=role_bep_it)
        self.save_data()
        await inter.response.send_message(
            embed=disnake.Embed(
                title="Setup des roles du servers",
                description=f"Role **ULB** : {self.ulb_guilds[inter.guild].role_ulb.mention if role_ulb else 'None'}\nRole **BEP** : {self.ulb_guilds[inter.guild].role_bep.mention if role_bep else 'None'}\nRole **BEP IT** : {self.ulb_guilds[inter.guild].role_bep_it.mention if role_bep_it else 'None'}",
            ).set_footer(text='Utilise "/role_update" pour mettre à jour les roles des membres de ce serveur.'),
            ephemeral=True,
        )

    async def update_member_roles(self, guildData: ULBGuild, member: disnake.Member):
        """Update the roles of a given member for a given guildData.

        Parameters
        ----------
        guildData : GuildData
            The data of the ulb Guild
        member : disnake.Member
            The member to update the roles
        """
        if member in self.ulb_users.keys():
            await member.add_roles(guildData.role_ulb)
            ulbUser_data = self.ulb_users.get(member)
            if ulbUser_data.bep:
                await member.add_roles(guildData.role_bep)
            if ulbUser_data.bep_it:
                await member.add_roles(guildData.role_bep_it)

    @roles.sub_command(name="update", description="Mettre à jour les roles des members de ce serveur.")
    async def roles_update(self, inter: ApplicationCommandInteraction):
        if inter.guild in self.ulb_guilds.keys():
            await inter.response.defer(ephemeral=True)
            guildData = self.ulb_guilds.get(inter.guild)
            if guildData:
                for member in inter.guild.members:
                    await self.update_member_roles(guildData, member)
            await inter.edit_original_response(embed=disnake.Embed(description="Mis à jour finie !"))
        else:
            await inter.response.send_message(
                embed=disnake.Embed(
                    description="""Les roles de ce serveur ne sont pas encore setup ! Utilise "**/roles setup**" pour sélectionner les roles."""
                ),
                ephemeral=True,
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, member: disnake.Member):
        if member.guild in self.ulb_guilds:
            if member not in self.ulb_users.keys():
                await member.send(
                    embed=disnake.Embed(
                        title=f"__Bienvenu sur le server **{member.guild.name}**__",
                        description="""Ce serveur est reservé aux étudiants de la faculté polytechnique de l'ULB. Pour acceder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB** en utilisant la commande "**/email**".""",
                        color=disnake.Color.teal(),
                    ).set_thumbnail(url=self.bot.BEP_image)
                )
            else:
                await self.update_member_roles(self.ulb_guilds.get(member.guild), member)

    @commands.user_command(name="add to bep", default_member_permissions=disnake.Permissions.all())
    async def add_to_bep(self, inter: disnake.UserCommandInteraction):
        if inter.target in self.ulb_users.keys():
            self.ulb_users.get(inter.target).bep = True
            self.save_data()
            await inter.response.send_message(
                embed=disnake.Embed(description=f"{inter.target.mention} à été ajouté aux membres du bep"),
                ephemeral=True,
            )
            for guild_data in self.ulb_guilds.values():
                await self.update_member_roles(guild_data, inter.target)
        else:
            inter.response.send_message(
                embed=disnake.Embed(
                    description=f"{inter.author.mention} n'a pas encore vérifié son addresse email ULB..."
                ),
                ephemeral=True,
            )

    @commands.user_command(name="add to bep IT", default_member_permissions=disnake.Permissions.all())
    async def add_to_bep_it(self, inter: disnake.UserCommandInteraction):
        if inter.target in self.ulb_users.keys():
            self.ulb_users.get(inter.target).bep_it = True
            self.save_data()
            await inter.response.send_message(
                embed=disnake.Embed(description=f"{inter.target.mention} à été ajouté aux membres du bep IT"),
                ephemeral=True,
            )
            for guild_data in self.ulb_guilds.values():
                await self.update_member_roles(guild_data, inter.target)
        else:
            inter.response.send_message(
                embed=disnake.Embed(
                    description=f"{inter.author.mention} n'a pas encore vérifié son addresse email ULB..."
                ),
                ephemeral=True,
            )

    @commands.user_command(name="add to ULB", default_member_permissions=disnake.Permissions.all())
    async def add_to_ulb(self, inter: disnake.UserCommandInteraction):
        if inter.target not in self.ulb_users.keys():
            await inter.response.send_modal(ForceRegisterModal(self, inter.target))
        else:
            await inter.response.send_message(
                embed=disnake.Embed(description=f"{inter.author.mention} à déjà vérifié son addresse email ULB..."),
                ephemeral=True,
            )

    @commands.Cog.listener("on_guild_join")
    async def on_member_join(self, guild: disnake.Guild):
        template_ids = [t.code for t in await guild.templates()]
        if os.getenv("GUILD_TEMPLATE_CODE") in template_ids:
            guildData = ULBGuild()
            at_least_one_role = False
            for role in guild.roles:
                if role.name == "ULB":
                    guildData.role_ulb = role
                    at_least_one_role = True
                if role.name == "BEP":
                    guildData.role_bep = role
                    at_least_one_role = True
                if role.name == "BEP IT":
                    guildData.role_bep_it = role
                    at_least_one_role = True
            if at_least_one_role:
                self.ulb_guilds[guild] = guildData


def setup(bot: commands.InteractionBot):
    bot.add_cog(Ulb(bot))
