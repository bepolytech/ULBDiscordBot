# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import secrets
import smtplib
from datetime import datetime
from typing import Coroutine
from typing import Dict
from typing import List

import disnake
from disnake.ext import commands

from .database import Database
from .database import DatabaseNotLoadedError
from .email import EmailManager
from .utils import update_user
from bot import Bot


class RegistrationNotSetError(Exception):
    """The Exception to be raise when the RegistrationForm class is used without have been set"""

    def __init__(self, *args: object) -> None:
        super().__init__("The RegistrationForm class need to be set with 'setup()' before being used !")


class CallbackModal(disnake.ui.Modal):
    """Represents a SubClass of UI Modal that allow to pass the callback coroutine as parameter

    .. versionadded:: 2.4

    Parameters
    ----------
    title: :class:`str`
        The title of the modal.
    components: |components_type|
        The components to display in the modal. Up to 5 action rows.
    custom_id: :class:`str`
        The custom ID of the modal.
    timeout: :class:`float`
        The time to wait until the modal is removed from cache, if no interaction is made.
        Modals without timeouts are not supported, since there's no event for when a modal is closed.
        Defaults to 600 seconds.
    callback: :class:`Coroutine`
        The corountine to be call as interaction callback. The coroutine only arg should be `disnake.ModalInteraction`.
    """

    def __init__(self, *, title: str, components: disnake.Component, timeout: float = 600, callback: Coroutine) -> None:
        super().__init__(title=title, components=components, timeout=timeout)
        self.callback_coro = callback

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await self.callback_coro(interaction)


class Registration:
    """Represent the Registration class


    Classmethods
    ------------
    setup(cog: `Ulb`): `func`
        Setup the Registration class. This need to be call before any instantiation
    new(inter: `disnake.ApplicationCommandInteraction,` target: `Optional[disnake.User]`): `coro`
        Create and start a new registration.
    """

    # Config params
    email_domains = "ulb.be"
    token_size = 10
    token_validity_time = 60 * 10  # In sec
    token_nbr_try = 5
    user_timeout_time = 60 * 5  # In sec

    # Class params
    _title = "Vérification de l'identité"
    _color = disnake.Colour.dark_blue()
    _contact_user: disnake.User = None
    _set = False

    _current_registrations: Dict[disnake.User, "Registration"] = {}
    _users_timeout: Dict[disnake.User, datetime] = {}

    @property
    def set(cls) -> bool:
        return cls._set

    @property
    def _current_registration_email(self) -> List[str]:
        return [reg.email for reg in self._current_registrations.values()]

    @classmethod
    async def _timeout_user(cls, user: disnake.User) -> None:
        cls._users_timeout[user] = datetime.now()
        await asyncio.sleep(cls.user_timeout_time)
        cls._users_timeout.pop(user)

    @classmethod
    def setup(cls, cog: commands.Cog) -> None:
        """Setup the Registration class

        Parameters
        ----------
        cog : Ulb
            The Ulb cog (with data loaded from googl sheet first)

        Raises
        ------
        `DatabaseNotLoadedError`
            Raise if the Database has not been load.
        """
        if Database.loaded == False:
            raise DatabaseNotLoadedError
        cls.contact_user = cog.bot.get_user(int(os.getenv("CONTACT_USER_ID")))  # FIXME: user never found
        cls.set = True

    @classmethod
    async def new(cls, inter: disnake.ApplicationCommandInteraction, target: disnake.User = None) -> None:
        """Followup response to an interaction by creating and sending a registrationForm for the target user.

        Parameters
        ----------
        inter : `disnake.ApplicationCommandInteraction`
            The slash command interaction that triggered the registration. This need to been reponse before since the registration form will user followup response
        target : `Optional[disnake.User]`
            The user to register. If `None`, then the inter.author is used.

        Raises
        ------
        `RegistrationFormaNotSetError`
            Raise if the RegistrationForm has not been setup.
        """
        if not cls.set:
            raise RegistrationNotSetError

        if not target:
            target = inter.author

        if target in cls._users_timeout.keys():
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title=cls._title,
                    description=f"Vous avez récement dépassé le nombre de tentative de vérification de votre adresse email.\nVous pourrez à nouveau essayer dans {(cls.user_timeout_time - (cls._users_timeout.get(target).second - datetime.now().second))//60} min",
                    color=disnake.Colour.orange(),
                ).set_thumbnail(Bot.ULB_image)
            )
            return

        new_form = Registration(target)
        await new_form._start(inter)

    def __init__(self, target: disnake.User) -> None:
        self.target = target
        self.email: str = None
        self.name: str = None
        self.token: str = None
        self.msg: disnake.Message = None
        self.nbr_try: int = 0

    async def _start(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Start a registration.

        If the user is already registered or in a pending registration procces, it send an error message and end this registration

        Otherwise it call `_start_registration_step()`.

        Parameters
        ----------
        inter : `disnake.ApplicationCommandInteraction`
            The slash command interaction that trigger the registration
        """

        ulb_user = Database.ulb_users.get(self.target, None)
        # Already registered
        if ulb_user:
            logging.info(f"[RegistrationForm] [User:{self.target.id}] Refused because user already registered.")
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self._title,
                    description=f"⛔ Tu es déjà associé à l'adresse email suivante : **{ulb_user.email}**.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.ULB_image)
            )
            return

        # Already a registration form pending
        pending_registration = self._current_registrations.get(self.target)
        if pending_registration:
            logging.info(f"[RegistrationForm] [User:{self.target.id}] Previous registration process cancelled.")
            await pending_registration._cancel()
            return
        self._current_registrations[self.target] = self

        logging.info(f"[RegistrationForm] [User:{self.target.id}] Registration started")
        await self._start_registration_step(inter)

    async def _start_registration_step(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Start the registration step by creating the necessary UI elements and send them as response to the interaction.

        Parameters
        ----------
        inter : `disnake.ApplicationCommandInteraction`
            The slash command interaction that trigger the step
        """
        # Create UI elements for registration
        self.registration_embed = disnake.Embed(
            title=self._title,
            description="> Ce serveur est réservé aux étudiants de l'ULB.\n> Pour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB**.",
            color=self._color,
        ).set_thumbnail(Bot.ULB_image)
        self.registration_view = disnake.ui.View()
        self.registration_button = disnake.ui.Button(
            label="Vérifier son identité", emoji="📧", style=disnake.ButtonStyle.primary
        )
        self.registration_button.callback = self._callback_registration_button
        self.registration_view.add_item(self.registration_button)
        self.registration_view.on_timeout = self._stop
        self.info_modal = CallbackModal(
            title=self._title,
            timeout=60 * 5,
            components=[
                disnake.ui.TextInput(
                    label="Addresse mail ULB (@ulb.be) :", custom_id="email", placeholder="ex : t.verhaegen@ulb.be"
                ),
            ],
            callback=self._callback_info_modal,
        )
        self.verification_embed = disnake.Embed(
            title=self._title, description=f"Vérification en cours...", color=self._color
        ).set_thumbnail(url=Bot.ULB_image)

        # Send the message with button
        self.msg = await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Registration view sent")

    async def _callback_registration_button(self, inter: disnake.MessageInteraction) -> None:
        """Send the registration modal when the registration button is triggered

        Parameters
        ----------
        inter : `disnake.MessageInteraction`
            The button interaction
        """
        self.registration_button.disabled = True
        await inter.response.send_modal(self.info_modal)
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Registration modal sent")

    async def _callback_info_modal(self, inter: disnake.ModalInteraction) -> None:
        """Check the validity of the email provided to the modal.

        If the email format or domain is not valid, the user is asked for it again.

        If the email is not available, it send a error message and end the registration.

        Otherwise, it call the `_start_token_verification_step()`

        Parameters
        ----------
        inter : `disnake.ModalInteraction`
            The modal interaction
        """
        self.msg = await inter.response.edit_message(embed=self.verification_embed, view=self.registration_view)
        logging.trace(
            f"[RegistrationForm] [User:{self.target.id}] Registration modal callback with email={inter.text_values.get('email')}"
        )

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
            logging.trace(f"[RegistrationForm] [User:{self.target.id}] Format not valid.")
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ Format incorrect",
                value=f"**{self.email}** n'est pas une adresse email valide.\nVérifie l'adresse email et réessaye.",
            )
            self.msg = await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        # Check email domain validity
        if splited_mail[1] not in self.email_domains:
            logging.trace(f"[RegistrationForm] [User:{self.target.id}] Domain not valid.")
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ Domaine incorrect",
                value=f"**{self.email}** n'est pas une adresse email **ULB**.\nUtilise ton adresse email **@ulb.be**.",
            )
            self.msg = await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        # Check email availablility from registered users
        for user_data in Database.ulb_users.values():
            if user_data.email == self.email:
                logging.trace(f"[RegistrationForm] [User:{self.target.id}] End because email not available")
                self.registration_embed.clear_fields()
                self.registration_embed.colour = disnake.Colour.red()
                self.registration_embed.remove_footer().add_field(
                    f"⛔ Adresse email non disponible",
                    value=f"**{self.email}** est déjà associée à un autre utilisateur discord.\nSi cette adresse email est bien la tienne et que quelqu'un a eu accès à ta boite mail pour se faire passer pour toi, envoie un message à {self._contact_user.mention if self._contact_user else 'un administrateur du serveur.'}.",
                )
                await inter.edit_original_message(embed=self.registration_embed, view=None)
                await self._stop()
                return

        # Valid and available
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Email valid and available.")
        await self._start_token_verification_step(inter)

    async def _start_token_verification_step(self, inter: disnake.ModalInteraction) -> None:
        """Start the token verification step by creating the necessary UI elements and send it to the user.

        It generate the token for the verification. If the token timeout, it send an error message and end the registration process.

        Parameters
        ----------
        inter : `disnake.ModalInteraction`
            The modal interaction that trigger the step
        """
        # Create UI elements for the token verification
        self.token_verification_embed = (
            disnake.Embed(
                title=self._title,
                description=f"""Un token à été envoyé à l'addresse email ***{self.email}***.""",
                color=self._color,
            )
            .set_thumbnail(url=Bot.ULB_image)
            .set_footer(text=f"""Le token est valide pendant {self.token_validity_time//60} minutes.""")
        )
        self.token_verification_view = disnake.ui.View()
        self.token_verification_button = disnake.ui.Button(
            label="Entrer le token", emoji="📧", style=disnake.ButtonStyle.primary
        )
        self.token_verification_button.callback = self._callback_token_verification_button
        self.token_verification_view.add_item(self.token_verification_button)
        self.token_verification_modal = CallbackModal(
            title=self._title,
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
            callback=self._callback_token_verification_modal,
        )

        # Send token verification message en button
        if not inter.response.is_done():
            self.msg = await inter.response.edit_message(
                embed=self.token_verification_embed, view=self.token_verification_view
            )
        else:
            self.msg = await inter.edit_original_message(
                embed=self.token_verification_embed, view=self.token_verification_view
            )
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token view sent.")
        self.token = secrets.token_hex(self.token_size)[: self.token_size]
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token generated.")
        try:
            EmailManager.send_token(self.email, self.token)
        except smtplib.SMTPSenderRefused as ex:
            logging.error(
                f"[EMAIL] {type(ex).__name__} occured during token email sending for email={self.email}: {ex}"
            )
            await inter.edit_original_response(
                embed=self.token_verification_embed.add_field(
                    name="❌",
                    value=f"Une erreur s'est produite durant l'envoie de l'email. Si cela se produit à nouveau, veuillez contacter {self._contact_user.mention if self._contact_user else 'un administrateur'}",
                ),
                view=None,
            )
            await self._stop()
        else:
            await asyncio.sleep(self.token_validity_time)
            if self.token:
                self.token = None
                logging.info(f"[RegistrationForm] [User:{self.target.id}] Token timeout.")
                await self._start_token_timeout_step(inter)

    async def _start_token_timeout_step(self, inter: disnake.ApplicationCommandInteraction) -> None:

        # Create UI elements for the token timeout step
        self.token_timeout_embed = disnake.Embed(
            title=self._title,
            description="""⚠️ Le token à expiré.\nDemandez un nouveau token ci-dessous.""",
            color=disnake.Colour.orange(),
        ).set_thumbnail(url=Bot.ULB_image)
        self.token_timeout_view = disnake.ui.View()
        self.token_timeout_button = disnake.ui.Button(
            label="Renvoyer un token", emoji="📧", style=disnake.ButtonStyle.primary
        )
        self.token_timeout_button.callback = self._start_token_verification_step
        self.token_timeout_view.add_item(self.token_timeout_button)

        self.msg = await inter.edit_original_response(embed=self.token_timeout_embed, view=self.token_timeout_view)

    async def _callback_token_verification_button(self, inter: disnake.MessageInteraction) -> None:
        """Send the token modal.

        If the token has timeout, it send an error message instead.

        Parameters
        ----------
        inter : `disnake.MessageInteraction`
            The button interaction
        """
        self.token_verification_button.disabled = True
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token button callback")
        await inter.response.send_modal(self.token_verification_modal)

    async def _callback_token_verification_modal(self, inter: disnake.ModalInteraction) -> None:
        """Check the token received from the modal.

        If the token has timeout, it send an error message.

        If the token is incorrect and the nbr of try is not exceed, it ask the user for it again.

        If the token is incorrect and the nbr of try is exceed, it send an error message and end the registration.

        Otherwise, it call `_register_user()`

        Parameters
        ----------
        inter : `disnake.ModalInteraction`
            The modal interaction
        """
        # If token has timeout
        if not self.token:
            await inter.response.defer(with_message=False)
            return

        self.msg = await inter.response.edit_message(embed=self.verification_embed, view=self.token_verification_view)
        token = inter.text_values.get("token")
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token modal callback with token={token}.")

        # If token invalid
        if token != self.token:
            logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token invalid")
            self.nbr_try += 1

            # End the registration
            if self.nbr_try >= self.token_nbr_try:
                logging.info(f"[RegistrationForm] [User:{self.target.id}] End because nbr of try for token exceed")
                self.token_verification_embed.clear_fields()
                self.token_verification_embed.colour = disnake.Colour.red()
                self.token_verification_embed.remove_footer().add_field(
                    name="⛔ Token invalide",
                    value=f"""Nombre de tentative dépassée.\nTu dois attendre {self.user_timeout_time//60} minutes avant de pouvoir recommencer.""",
                )
                await inter.edit_original_message(
                    embed=self.token_verification_embed,
                    view=None,
                )
                asyncio.create_task(self._timeout_user(self.target))
                await self._stop()
                return

            # Ask for it again
            else:
                self.token_verification_button.disabled = False
                self.token_verification_embed.clear_fields()
                self.token_verification_embed.add_field(
                    name="⚠️ Token invalide !",
                    value="Si tu as fait plusieurs tentatives de vérification, utilise bien le dernier token que tu as reçu.",
                )
                self.msg = await inter.edit_original_message(
                    embed=self.token_verification_embed,
                    view=self.token_verification_view,
                )
            return

        # Check email availablility from registered users again, if the case two user register with the same email at the same time
        for user_data in Database.ulb_users.values():
            if user_data.email == self.email:
                logging.trace(f"[RegistrationForm] [User:{self.target.id}] End because email not available")
                self.token_verification_embed.clear_fields()
                self.token_verification_embed.colour = disnake.Colour.red()
                self.token_verification_embed.remove_footer().add_field(
                    f"⛔ Adresse email non disponible",
                    value=f"**{self.email}** est déjà associée à un autre utilisateur discord.\nSi cette adresse email est bien la tienne et que quelqu'un a eu accès à ta boite mail pour se faire passer pour toi, envoie un message à {self._contact_user.mention if self._contact_user else 'un administrateur du serveur.'}.",
                )
                await inter.edit_original_message(embed=self.token_verification_embed, view=None)
                await self._stop()
                return

        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Token valid")
        await self._register_user_step(inter)

    async def _register_user_step(self, inter: disnake.ModalInteraction) -> None:
        """Register the user.

        It extract the name of the user from the email, save it to the google sheet, send a confirmation message, then add role and edit nickname for all ulb guilds where the user is.

        Parameters
        ----------
        inter : `disnake.ModalInteraction`
            The modal interaction that triggered the step
        """
        # Extract name and store the user
        name = " ".join([name.title() for name in self.email.split("@")[0].split(".")])
        logging.trace(f"[RegistrationForm] [User:{self.target.id}] Extracted name from email= {name}")
        Database.set_user(self.target, name, self.email)
        await self._stop()
        logging.info(f"[RegistrationForm] [User:{self.target.id}] Registration succeed")

        # Send confirmation message
        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"✅ {self._title}",
                description="Ton addresse mail **ULB** est bien vérifiée !\nTu as désormais accès aux serveurs **ULB**",
                color=disnake.Color.green(),
            ).set_thumbnail(url=Bot.ULB_image),
            view=None,
        )

        await update_user(self.target, name=name)

    async def _cancel(self) -> None:
        await self._stop()
        await self.msg.edit(
            embed=disnake.Embed(
                title=self._title, description="Vérification abandonnée.", color=disnake.Colour.dark_grey()
            )
        )

    async def _stop(self) -> None:
        """Properly end a registration process by deleting the related pending registration entries."""
        self._current_registrations.pop(self.target)


class AdminAddUserModal(disnake.ui.Modal):

    _email_default_value = "N/A"

    def __init__(self, user: disnake.User) -> None:
        self.user = user
        components = [
            disnake.ui.TextInput(label="Prenom + Nom", custom_id="name"),
            disnake.ui.TextInput(label="Adresse email (optional)", custom_id="email", required=False),
        ]
        super().__init__(title=f"Ajout d'un utilisateur", components=components, timeout=10 * 60)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(ephemeral=True)
        name = interaction.text_values.get("name")
        email = interaction.text_values.get("email", self._email_default_value)
        Database.set_user(self.user, name, email)
        await interaction.edit_original_response(
            embed=disnake.Embed(
                description=f"{self.user.mention} a bien été ajouté à la base de donnée", color=disnake.Color.green()
            )
        )

        await update_user(self.user, name=name)


class AdminEditUserModal(disnake.ui.Modal):

    _email_default_value = "N/A"

    def __init__(self, user: disnake.User) -> None:
        self.user = user
        user_data = Database.ulb_users.get(user)
        components = [
            disnake.ui.TextInput(label="Prenom + Nom", custom_id="name", value=user_data.name),
            disnake.ui.TextInput(
                label="Adresse email (optional)",
                custom_id="email",
                value=user_data.email if user_data.email != self._email_default_value else None,
                required=False,
            ),
        ]

        super().__init__(title=f"Mis à jour d'un utilisateur", components=components, timeout=10 * 60)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(ephemeral=True)
        name = interaction.text_values.get("name")
        email = interaction.text_values.get("email", self._email_default_value)
        Database.set_user(self.user, name, email)

        await interaction.edit_original_response(
            embed=disnake.Embed(
                description=f"{self.user.mention} a bien été mis à jour dans la base de donnée",
                color=disnake.Color.green(),
            )
        )

        await update_user(self.user, name=name)
