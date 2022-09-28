# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import secrets
from typing import Coroutine
from typing import List

import disnake
from disnake.ext import commands

from .email import EmailManager
from .googleSheet import GoogleSheetManager
from .googleSheet import GoogleSheetManagerNotLoadedError
from .utils import update_user
from bot import Bot


class RegistrationFormaNotSetError(Exception):
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


# TODO: add message_jump_irl to error message for pending registration case (and check timeout behaviour)
class RegistrationForm:
    """Represent the RegistrationForm


    Classmethods
    ------------
    setup(cog: `Ulb`): `func`
        Setup the RegistrationForm class. This need to be call before any instantiation
    new(inter: `disnake.ApplicationCommandInteraction,` target: `Optional[disnake.User]`): `coro`
        Create and start a new registration form.
    """

    email_domain = "ulb.be"
    token_size = 10
    token_validity_time = 60 * 10  # In sec
    token_nbr_try = 2
    interaction_validity_time = 60 * 10

    title = "Vérification de l'identité"
    color = disnake.Colour.dark_blue()
    pending_registration_emails: List[str] = []
    pending_registration_users: List[disnake.User] = []
    contact_user: disnake.User = None
    _set = False

    @property
    def set(cls) -> bool:
        return cls._set

    @classmethod
    def setup(cls, cog: commands.Cog) -> None:
        """Setup the RegistrationForm class

        Parameters
        ----------
        cog : Ulb
            The Ulb cog (with data loaded from googl sheet first)

        Raises
        ------
        `GoogleSheetManagerNotLoadedError`
            Raise if the GoogleSheetManager has not been load.
        """
        if GoogleSheetManager.loaded == False:
            raise GoogleSheetManagerNotLoadedError
        cls.contact_user = cog.bot.get_user(int(os.getenv("CONTACT_USER_ID")))
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
            raise RegistrationFormaNotSetError
        if not target:
            target = inter.author
        new_form = RegistrationForm(target)
        await new_form._start(inter)

    def __init__(self, target: disnake.User) -> None:
        self.target = target
        self.email = None
        self.name = None
        self.token = None
        self.nbr_try = 0

    async def _start(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Start a registration.

        If the user is already registered or in a pending registration procces, it send an error message and end this registration

        Otherwise it call `_start_registration_step()`.

        Parameters
        ----------
        inter : `disnake.ApplicationCommandInteraction`
            The slash command interaction that trigger the registration
        """
        ulb_user = GoogleSheetManager.ulb_users.get(self.target, None)
        # Already registered
        if ulb_user:
            logging.info(f"[RegistrationForm] [User:{self.target.id}] Refused because user already registered.")
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self.title,
                    description=f"Tu es déjà associé à l'adresse email suivante : **{ulb_user.email}**.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image)
            )
            return

        # Already a registration form pending
        if self.target in self.pending_registration_users:
            logging.info(
                f"[RegistrationForm] [User:{self.target.id}] Refused because user in another pending registration."
            )
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self.title,
                    description=f"Tu as déjà une vérification en cours. Termine celle-ci ou attends quelques minutes avant de réessayer.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image)
            )
            return

        self.pending_registration_users.append(self.target)
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
        self.registration_embed = (
            disnake.Embed(
                title=self.title,
                description="> Ce serveur est réservé aux étudiants de l'ULB.\n> Pour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB**.",
                color=self.color,
            )
            .set_thumbnail(Bot.BEP_image)
            .set_footer(text=f"Ce message est valide pendant {self.interaction_validity_time//60} minutes.")
        )
        self.registration_view = disnake.ui.View(timeout=self.interaction_validity_time)
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

        # Send the message with button
        await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Registration view sent")

    async def _callback_registration_button(self, inter: disnake.MessageInteraction) -> None:
        """Send the registration modal when the registration button is triggered

        Parameters
        ----------
        inter : `disnake.MessageInteraction`
            The button interaction
        """
        self.registration_button.disabled = True
        await inter.response.send_modal(self.info_modal)
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Registration modal sent")

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
        await inter.response.edit_message(embed=self.verification_embed, view=self.registration_view)
        self.email = inter.text_values.get("email")
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Registration modal callback with email={self.email}")

        # Check email format validity
        splited_mail: List[str] = self.email.split("@")
        if (
            len(splited_mail) != 2
            or len(splited_mail[0]) == 0
            or len(splited_mail[1].split(".")) != 2
            or len(splited_mail[1].split(".")[0]) == 0
            or splited_mail[1].split(".")[1] == 0
        ):
            logging.debug(f"[RegistrationForm] [User:{self.target.id}] Format not valid.")
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ Format incorrect",
                value=f"**{self.email}** n'est pas une adresse email valide.\nVérifie l'adresse email et réessaye.",
            )
            await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        # Check email domain validity
        if splited_mail[1] != self.email_domain:
            logging.debug(f"[RegistrationForm] [User:{self.target.id}] Domain not valid.")
            self.registration_button.disabled = False
            self.registration_embed.clear_fields()
            self.registration_embed.add_field(
                f"⚠️ Domaine incorrect",
                value=f"**{self.email}** n'est pas une adresse email **ULB**.\nUtilise ton adresse email **@ulb.be**.",
            )
            await inter.edit_original_message(embed=self.registration_embed, view=self.registration_view)
            return

        # Check email availablility from registered users
        for user_data in GoogleSheetManager.ulb_users.values():
            if user_data.email == self.email:
                logging.debug(f"[RegistrationForm] [User:{self.target.id}] End because email not available")
                self.registration_embed.clear_fields()
                self.registration_embed.remove_footer().add_field(
                    f"⛔ Adresse email non disponible",
                    value=f"**{self.email}** est déjà associée à un autre utilisateur discord.\nSi cette adresse email est bien la tienne et que quelqu'un a eu accès à ta boite mail pour se faire passer pour toi, envoie un message à {self.contact_user.mention if self.contact_user else 'un administrateur du serveur.'}.",
                )
                await inter.edit_original_message(embed=self.registration_embed, view=None)
                await self._stop()
                return

        # Check email availablility from pending registration
        if self.email in self.pending_registration_emails:
            logging.info(
                f"[RegistrationForm] [User:{self.target.id}] End because email in another pending registration."
            )
            self.registration_embed.clear_fields()
            self.registration_embed.remove_footer().add_field(
                f"⛔ Adresse email non disponible",
                value=f"L'adresse email {self.email} est déjà en cours de vérification.\nTermine la vérification en cours ou bien attends quelques minutes avant de réessayer.",
            )
            await inter.edit_original_message(embed=self.registration_embed, view=None)
            await self._stop()
            return

        # Valid and available
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Email valid and available.")
        self.pending_registration_emails.append(self.email)
        self.token = secrets.token_hex(self.token_size)[: self.token_size]
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token={self.token} generate.")
        await self._start_token_verification_step(inter)

    async def _start_token_verification_step(self, inter: disnake.ModalInteraction) -> None:
        """Start the token verification step by creating the necessary UI elements and send it to the user.

        It generate the token for the verification. If the token timeout, it send an error message and end the registration process.

        Parameters
        ----------
        inter : `disnake.ModalInteraction`
            The modal interaction that trigger the step
        """
        print()
        # Create UI elements for the token verification
        self.token_embed = (
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

        self.token_timeout_embed = disnake.Embed(
            title=self.title,
            description="""⛔ **Le token à expiré.**\nUtilise **"/email"** à nouveau pour réessayer.""",
            color=disnake.Colour.orange(),
        )

        # Send token verification message en button
        await inter.edit_original_message(embed=self.token_embed, view=self.token_view)
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token view sent.")
        EmailManager.send_token(self.email, self.token)
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Email sent")
        await asyncio.sleep(self.token_validity_time)
        if self.token:
            self.token = None
            logging.info(f"[RegistrationForm] [User:{self.target.id}] Token timeout.")
            await inter.edit_original_message(embed=self.token_timeout_embed, view=None)
            await self._stop()

    async def _callback_token_button(self, inter: disnake.MessageInteraction) -> None:
        """Send the token modal.

        If the token has timeout, it send an error message instead.

        Parameters
        ----------
        inter : `disnake.MessageInteraction`
            The button interaction
        """
        self.token_button.disabled = True
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token button callback")

        # If token has timeout
        if not self.token:
            await inter.response.edit_message(embed=self.token_timeout_embed, view=None)
            return

        await inter.response.send_modal(self.token_modal)

    async def _callback_token_modal(self, inter: disnake.ModalInteraction) -> None:
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
            await inter.response.edit_message(embed=self.token_timeout_embed, view=None)
            return

        await inter.response.edit_message(embed=self.verification_embed, view=self.token_view)
        token = inter.text_values.get("token")
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token modal callback with token={token}.")

        # If token invalid
        if token != self.token:
            logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token invalid")
            self.nbr_try += 1

            # End the registration
            if self.nbr_try >= self.token_nbr_try:
                logging.info(f"[RegistrationForm] [User:{self.target.id}] End because nbr of try for token exceed")
                self.token_embed.clear_fields()
                self.token_embed.remove_footer().add_field(
                    name="⛔ Token invalide",
                    value="""Nombre de tentative dépassé. **"/email"** pour recommencer.""",
                )
                await inter.edit_original_message(
                    embed=self.token_embed,
                    view=None,
                )
                await self._stop()
                return

            # Ask for it again
            else:
                self.token_button.disabled = False
                self.token_embed.clear_fields()
                self.token_embed.add_field(
                    name="⚠️ Token invalide !",
                    value="Si tu as fait plusieurs tentative de vérification, utilise bien le dernier token que tu as reçu.",
                )
                await inter.edit_original_message(
                    embed=self.token_embed,
                    view=self.token_view,
                )
            return

        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Token valid")
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
        logging.debug(f"[RegistrationForm] [User:{self.target.id}] Extracted name from email= {name}")
        GoogleSheetManager.set_user(self.target, name, self.email)
        await self._stop()
        logging.info(f"[RegistrationForm] [User:{self.target.id}] Registration succeed")

        # Send confirmation message
        await inter.edit_original_message(
            embed=disnake.Embed(
                title=f"✅ {self.title}",
                description="Ton addresse mail **ULB** est bien vérifiée !\nTu as désormais accès aux serveurs **ULB**",
                color=disnake.Color.green(),
            ).set_thumbnail(url=Bot.BEP_image),
            View=None,
        )

        await update_user(self.target, name)

    async def _stop(self) -> None:
        """Properly end a registration process by deleting the related pending registration entries."""
        try:
            self.pending_registration_users.remove(self.target)
        except ValueError:
            pass
        if self.email:
            try:
                self.pending_registration_emails.remove(self.email)
            except ValueError:
                pass


class AdminAddUserModal(disnake.ui.Modal):

    _email_default_value = "N/A"

    def __init__(self, user: disnake.User) -> None:
        self.user = user
        components = [
            disnake.ui.TextInput(label="Prenom + Nom", custom_id="name"),
            disnake.ui.TextInput(label="Adresse email (optional)", custom_id="email", required=False),
        ]
        super().__init__(title=f"Ajout de l'utilisateur id = {user.id}", components=components, timeout=10 * 60)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(ephemeral=True)
        name = interaction.text_values.get("name")
        email = interaction.text_values.get("email", self._email_default_value)
        GoogleSheetManager.set_user(self.user, name, email)
        await interaction.edit_original_response(
            embed=disnake.Embed(
                description=f"{self.user.mention} a bien été ajouté à la base de donnée", color=disnake.Color.green()
            )
        )

        await update_user(self.user, name)


class AdminEditUserModal(disnake.ui.Modal):

    _email_default_value = "N/A"

    def __init__(self, user: disnake.User) -> None:
        self.user = user
        user_data = GoogleSheetManager.ulb_users.get(user)
        components = [
            disnake.ui.TextInput(label="Prenom + Nom", custom_id="name", value=user.data.name),
            disnake.ui.TextInput(
                label="Adresse email (optional)",
                custom_id="email",
                value=user_data.email if user_data.email != self._email_default_value else None,
                required=False,
            ),
        ]

        super().__init__(title=f"Mis à jour de l'utilisateur id = {user.id}", components=components, timeout=10 * 60)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(ephemeral=True)
        name = interaction.text_values.get("name")
        email = interaction.text_values.get("email", self._email_default_value)
        GoogleSheetManager.set_user(self.user, name, email)

        await interaction.edit_original_response(
            embed=disnake.Embed(
                description=f"{self.user.mention} a bien été mis à jour dans la base de donnée",
                color=disnake.Color.green(),
            )
        )

        await update_user(self.user, name)
