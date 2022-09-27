# -*- coding: utf-8 -*-
import logging
import os
import secrets
from typing import Coroutine
from typing import Dict
from typing import List

import disnake
from disnake.client import HTTPException
from disnake.ext import commands

from .email import EmailManager
from .ULBUser import ULBUser
from bot import Bot
from cogs.Ulb.googleSheet import GoogleSheetManager


class CallbackModal(disnake.ui.Modal):
    """Subclass of disnake.ui.Modal that allow to pass a coro as to be call for callback"""

    def __init__(self, *, title: str, components: disnake.Component, timeout: float = 600, callback: Coroutine) -> None:
        super().__init__(title=title, components=components, timeout=timeout)
        self.callback_coro = callback

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await self.callback_coro(interaction)


# TODO real token timeout + number of try


class RegistrationForm:

    email_domain = "ulb.be"

    token_size: int = 10
    token_validity_time: int = 60 * 1  # In sec
    timeout_duration = 60 * 1

    title = "Vérification de l'identité"
    color = disnake.Colour.dark_blue()
    
    ulb_users: Dict[disnake.User, ULBUser] = None
    ulb_guilds: Dict[disnake.Guild, disnake.Role] = None
    pending_registration_emails: List[str]  = None
    pending_registration_users: List[disnake.User] = None
    contact_user: disnake.User = None
    set = False
    
    @classmethod
    def setup(cls, cog: commands.Cog):
        """Setup the RegistrationForm class

        Parameters
        ----------
        cog : Ulb
            The Ulb cog (with data loaded from googl sheet first)

        Raises
        ------
        `AttributeError`
            Raise if the Ulb cog data has not been load yet.
        """
        if GoogleSheetManager.loaded == False:
            logging.error("You have to load data from google sheet before calling setup for the RegistrationForm class")
            raise AttributeError
        cls.ulb_users = cog.ulb_users
        cls.ulb_guilds = cog.ulb_guilds
        cls.pending_registration_emails = cog.pending_registration_emails
        cls.pending_registration_users = cog.pending_registration_users
        cls.contact_user = cog.bot.get_user(int(os.getenv('BEP_USER_ID')))
        cls.set = True
        
    @classmethod
    async def new(cls, inter: disnake.ApplicationCommandInteraction, target: disnake.User = None):
        """Followup response to an interaction by creating and sending a registrationForm for the target user.

        Parameters
        ----------
        inter : `disnake.ApplicationCommandInteraction`
            The interaction to response to. This has to been reponse before since the registration form will user followup response
        target : `Optional[disnake.User]`
            The user to register. If `None`, then the inter.author is used.

        Raises
        ------
        `AttributeError`
            Raise if the RegistrationForm has not been setup yet
        """
        if not cls.set:
            logging.error("RegistrationForm need to be 'setup' before being called")
            raise AttributeError
        if not target:
            target = inter.author
        new_form = RegistrationForm(target)
        await new_form._send(inter)
        

    def __init__(self, target: disnake.User):
        self.target = target
        self.email = None
        self.name = None
        self.token = None
        self._init_UI()

    def _init_UI(self):
        self.registration_embed = (
            disnake.Embed(
                title=self.title,
                description="> Ce serveur est réservé aux étudiants de l'ULB.\n> Pour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB**.",
                color=self.color,
            )
            .set_thumbnail(Bot.BEP_image)
            .set_footer(text=f"Ce message est valide pendant {self.timeout_duration//60} minutes.")
        )

        self.registration_view = disnake.ui.View(timeout=self.timeout_duration)
        self.registration_button = disnake.ui.Button(
            label="Vérifier son identité", emoji="📧", style=disnake.ButtonStyle.primary
        )
        self.registration_button.callback = self._callback_registration_button
        self.registration_view.add_item(self.registration_button)
        self.registration_view.on_timeout = self._stop

        self.info_modal = CallbackModal(
            title=self.title,
            timeout=60 * 5,
            components=[
                disnake.ui.TextInput(
                    label="Addresse mail ULB (@ulb.be) :", custom_id="email", placeholder="ex : t.verhaegen@ulb.be"
                ),
            ],
            callback=self._callback_info_modal,
        )

        self.verification_embed = disnake.Embed(
            title=self.title, description=f"Vérification en cours...", color=self.color
        ).set_thumbnail(url=Bot.BEP_image)

        self.token_view = disnake.ui.View(timeout=self.token_validity_time)
        self.token_button = disnake.ui.Button(label="Entrer le token", emoji="📧", style=disnake.ButtonStyle.primary)
        self.token_button.callback = self._callback_token_button
        self.token_view.add_item(self.token_button)
        self.token_view.on_timeout = self._stop

        self.token_modal = CallbackModal(
            title=self.title,
            timeout=60 * 5,
            components=[
                disnake.ui.TextInput(
                    label=f"Entre ton token de vérification",
                    custom_id="token",
                    placeholder=f"Token de {self.token_size} caractères",
                    min_length=self.token_size,
                    max_length=self.token_size,
                )
            ],
            callback=self._callback_token_modal,
        )

        self.confirmation_embed = disnake.Embed(
            title=f"✅ {self.title}",
            description="Ton addresse mail **ULB** est bien vérifiée !\nTu as désormais accès aux serveurs **ULB**",
            color=disnake.Color.green(),
        ).set_thumbnail(url=Bot.BEP_image)

    @property
    def _token_embed(self) -> disnake.Embed:
        return (
            disnake.Embed(
                title=self.title,
                description=f"""Un token à été envoyé à l'addresse email ***{self.email}***.""",
                color=self.color,
            )
            .set_thumbnail(url=Bot.BEP_image)
            .set_footer(
                text=f"""Le token est valide pendant {self.token_validity_time//60} minutes, tout comme le bouton sous ce message."""
            )
        )

    async def _send(self, inter: disnake.ApplicationCommandInteraction):
        if self.target in self.ulb_users.keys():
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self.title,
                    description=f"Tu es déjà associé à l'adresse email suivante : **{self.ulb_users.get(self.target).email}**.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image)
            )
            return

        if self.target in self.pending_registration_users:
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self.title,
                    description=f"Tu as déjà une vérification en cours. Termine celle-ci ou attends quelques minutes avant de réessayer.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image)
            )
            return

        self.pending_registration_users.append(self.target)
        await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)

    async def _callback_registration_button(self, inter: disnake.MessageInteraction):
        self.registration_button.disabled = True
        await inter.response.send_modal(self.info_modal)

    async def _callback_info_modal(self, inter: disnake.ModalInteraction):
        await inter.response.edit_message(embed=self.verification_embed, view=self.registration_view)
        self.email = inter.text_values.get("email")

        # Check email format validity
        splited_mail: List[str] = self.email.split("@")
        if (
            len(splited_mail) != 2
            or len(splited_mail[0]) == 0
            or len(splited_mail[1].split(".")) != 2
            or len(splited_mail[1].split(".")[0]) == 0
            or splited_mail[1].split(".")[1] == 0
        ):
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ **{self.email}** n'est pas une adresse email valide", value="Vérifie l'adresse email et réessaye."
            )
            await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        # Check email domain validity
        if splited_mail[1] != self.email_domain:
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ **{self.email}** n'est pas une adresse email **ULB**",
                value="Utilise ton adresse email **@ulb.be**.",
            )
            await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        #Check email available
        for user_data in self.ulb_users.values():
            if user_data.email == self.email:
                self.registration_embed.clear_fields()
                self.registration_embed.add_field(
                    f"⛔ **{self.email}** est déjà associée à un autre utilisateur discord",
                    value=f"Si cette adresse email est bien la tienne et que quelqu'un a eu accès à ta boite mail pour se faire passer pour toi, envoie un message à {self.bot.get_user(int(os.getenv('BEP_USER_ID'))) if self.bot.get_user(int(os.getenv('BEP_USER_ID'))) else '**@Bureau Etudiant Polytechnique**'}.",
                )
                await inter.edit_original_message(embed=self.registration_embed, view=None)
                await self._stop()
                return

        # Check if pending registration for this email
        if self.email in self.pending_registration_emails:
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⛔  L'adresse email {self.email} est déjà en cours de vérification",
                value=f"Termine la vérification en cours ou bien attends quelques minutes avant de réessayer.",
            )
            await inter.edit_original_message(embed=self.registration_embed, view=None)
            await self._stop()
            return

        # Valid and available
        self.pending_registration_emails.append(self.email)
        self.token = secrets.token_hex(self.token_size)[: self.token_size]
        await inter.edit_original_message(embed=self._token_embed, view=self.token_view)
        EmailManager.sendToken(self.email, self.token)

    async def _callback_token_button(self, inter: disnake.MessageInteraction):
        self.token_button.disabled = True
        await inter.response.send_modal(self.token_modal)

    async def _callback_token_modal(self, inter: disnake.ModalInteraction):
        await inter.response.edit_message(embed=self.verification_embed, view=self.token_view)
        token = inter.text_values.get("token")
        if token != self.token:
            self.token_button.disabled = False
            self._token_embed.add_field(
                name="⚠️ Token invalide !",
                value="Si tu as fait plusieurs tentative de vérification, utilise bien le dernier token que tu as reçu.",
            )
            await inter.edit_original_message(
                embed=self._token_embed,
                view=self.token_view,
            )
            return

        name = " ".join([name.title() for name in self.email.split("@")[0].split(".")])
        GoogleSheetManager.set_user(self.target.id, name, self.email)
        self.ulb_users.setdefault(self.target, ULBUser(name, self.email))
        self.pending_registration_emails.remove(self.email)
        self.pending_registration_users.remove(self.target)

        for guild, role in self.ulb_guilds.items():
            member = guild.get_member(self.target.id)
            if member:
                try:
                    await member.add_roles(role)
                except HTTPException as ex:
                    logging.error(
                        f'Error adding ulb role "{role.name}:{role.id}" from guild "{guild.name}:{guild.id}" to ulb user "{self.target.name}:{self.target.id}": {ex}'
                    )
                try:
                    await member.edit(nick=f"{name}")
                except HTTPException as ex:
                    logging.warning(f'Error editing user "{self.target.name}:{self.target.id}" nick to "{name}": {ex}')

        await inter.edit_original_message(
            embed=self.confirmation_embed,
            view=None,
        )

    async def _stop(self):
        try:
            self.pending_registration_users.remove(self.target)
        except ValueError:
            pass
        if self.email:
            try:
                self.pending_registration_emails.remove(self.email)
            except ValueError:
                pass
