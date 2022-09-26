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

from .emailManager import EmailManager
from .ULBUser import ULBUser
from bot import Bot


class CallbackModal(disnake.ui.Modal):
    """Subclass of disnake.ui.Modal that allow to pass a coro as to be call for callback"""

    def __init__(self, *, title: str, components: disnake.Component, timeout: float = 600, callback: Coroutine) -> None:
        super().__init__(title=title, components=components, timeout=timeout)
        self.callback_coro = callback

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await self.callback_coro(interaction)


class RegistrationForm:

    email_domain = "ulb.be"

    token_size: int = 10
    token_validity_time: int = 10 * 60  # In sec
    timeout_duration = 60 * 10

    title = "Vérification de l'identité"
    color = disnake.Colour.dark_blue()

    emailManager = EmailManager()

    disclaimer_embed = (
        disnake.Embed(
            title=title,
            description="> Ce serveur est réservé aux étudiants de l'ULB.\n> Pour accéder à ce serveur, tu dois vérifier ton identité avec ton addresse email **ULB**.",
            color=color,
        )
        .set_thumbnail(Bot.BEP_image)
        .set_footer(text=f"Ce message est valide pendant {timeout_duration//60} minutes.")
    )

    verification_embed = disnake.Embed(title=title, description=f"Vérification en cours...", color=color).set_thumbnail(
        url=Bot.BEP_image
    )

    confirmation_embed = disnake.Embed(
        title=f"✅ {title}",
        description="Ton addresse mail **ULB** est bien vérifiée !\nTu as désormais accès aux serveurs **ULB**",
        color=disnake.Color.green(),
    ).set_thumbnail(url=Bot.BEP_image)

    def __init__(self, target: disnake.User, cog: commands.Cog):
        self.target = target
        self.pending_registration_users: List[disnake.User] = cog.pending_registration_users
        self.pending_registration_emails: List[str] = cog.pending_registration_emails
        self.ulb_users: Dict[disnake.User, ULBUser] = cog.ulb_users
        self.ulb_guilds: Dict[disnake.Guild, disnake.Role] = cog.ulb_guilds
        self.bot: Bot = cog.bot
        self.cog = cog
        self.init_UI()

    def init_UI(self):
        self.registration_view = disnake.ui.View(timeout=self.timeout_duration)
        self.registration_button = disnake.ui.Button(
            label="Vérifier son identité", emoji="📧", style=disnake.ButtonStyle.primary
        )
        self.registration_button.callback = self.callback_registration_button
        self.registration_view.add_item(self.registration_button)
        self.registration_view.on_timeout = self.on_timeout

        self.info_modal = CallbackModal(
            title=self.title,
            timeout=60 * 5,
            components=[
                disnake.ui.TextInput(
                    label="Addresse mail ULB (@ulb.be) :", custom_id="email", placeholder="ex : t.verhaegen@ulb.be"
                ),
            ],
            callback=self.callback_info_modal,
        )

        self.token_view = disnake.ui.View(timeout=self.token_validity_time)
        self.token_button = disnake.ui.Button(label="Entrer le token", emoji="📧", style=disnake.ButtonStyle.primary)
        self.token_button.callback = self.callback_token_button
        self.token_view.add_item(self.token_button)
        self.token_view.on_timeout = self.on_timeout

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
            callback=self.callback_token_modal,
        )

    @property
    def token_embed(self) -> disnake.Embed:
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

    async def start(self, inter: disnake.ApplicationCommandInteraction):
        if self.target in self.ulb_users.keys():
            await inter.edit_original_message(
                embed=disnake.Embed(
                    title=self.title,
                    description=f"Tu es déjà associé à l'adresse email suivante : **{self.ulb_users.get(self.target).email}**.",
                    color=disnake.Colour.dark_orange(),
                ).set_thumbnail(Bot.BEP_image)
            )
            return
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
        await inter.edit_original_message(embed=self.disclaimer_embed, view=self.registration_view)

    async def callback_registration_button(self, inter: disnake.MessageInteraction):
        self.registration_button.disabled = True
        await inter.response.send_modal(self.info_modal)

    async def callback_info_modal(self, inter: disnake.ModalInteraction):
        await inter.response.edit_message(embed=self.verification_embed, view=self.registration_view)
        self.email = inter.text_values.get("email")

        # Check if email format valid
        splited_mail: List[str] = self.email.split("@")
        if len(splited_mail) != 2:
            self.registration_button.disabled = False
            self.disclaimer_embed.clear_fields()
            self.disclaimer_embed.add_field(
                f"⚠️ **{self.email}** n'est pas une adresse email valide", value="Vérifie l'adresse email et réessaye."
            )
            await inter.edit_original_message(embed=self.disclaimer_embed, view=self.registration_view)
            return

        # Check ulb domain
        if splited_mail[1] != self.email_domain:
            self.registration_button.disabled = False
            self.disclaimer_embed.clear_fields()
            self.disclaimer_embed.add_field(
                f"⚠️ **{self.email}** n'est pas une adresse email **ULB**",
                value="Utilise ton adresse email **@ulb.be**.",
            )
            await inter.edit_original_message(embed=self.disclaimer_embed, view=self.registration_view)
            return

        for user_data in self.ulb_users.values():
            if user_data.email == self.email:
                self.disclaimer_embed.clear_fields()
                self.disclaimer_embed.add_field(
                    f"⛔ **{self.email}** est déjà associée à un autre utilisateur discord",
                    value=f"Si cette adresse email est bien la tienne et que quelqu'un a eu accès à ta boite mail pour se faire passer pour toi, envoie un message à {self.bot.get_user(int(os.getenv('BEP_USER_ID'))) if self.bot.get_user(int(os.getenv('BEP_USER_ID'))) else '@Bureau Etudiant Polytechnique'}.",
                )
                await inter.edit_original_message(embed=self.disclaimer_embed, view=None)
                return

        # Check if pending registration for this email
        if self.email in self.pending_registration_emails:
            self.disclaimer_embed.clear_fields()
            self.disclaimer_embed.add_field(
                f"⛔  L'adresse email {self.email} est déjà en cours de vérification",
                value=f"Termine la vérification en cours ou bien attends quelques minutes avant de réessayer.",
            )
            await inter.edit_original_message(embed=self.disclaimer_embed, view=None)
            return

        # Valid and available
        self.pending_registration_emails.append(self.email)
        self.token = secrets.token_hex(self.token_size)[: self.token_size]
        print(self.token)
        await inter.edit_original_message(embed=self.token_embed, view=self.token_view)
        self.emailManager.sendToken(self.email, self.token)

    async def callback_token_button(self, inter: disnake.MessageInteraction):
        self.token_button.disabled = True
        await inter.response.send_modal(self.token_modal)

    async def callback_token_modal(self, inter: disnake.ModalInteraction):
        await inter.response.edit_message(embed=self.verification_embed, view=self.token_view)
        token = inter.text_values.get("token")
        if token != self.token:
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

        name = " ".join([name.title() for name in self.email.split("@")[0].split(".")])
        self.ulb_users.setdefault(self.target, ULBUser(name, self.email))
        self.cog.save_data()
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

    async def on_timeout(self):
        try:
            self.pending_registration_users.remove(self.target)
        except ValueError:
            pass
        if self.email:
            try:
                self.pending_registration_emails.remove(self.email)
            except ValueError:
                pass
