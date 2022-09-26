# -*- coding: utf-8 -*-
import asyncio

import disnake

from bot import Bot

title = "Vérification de l'identité"


class RegisterView(disnake.ui.View):
    def __init__(self, mailCog):
        super().__init__(timeout=60 * 20)
        self.mailCog = mailCog

    @disnake.ui.button(label="Vérifier son identité", emoji="📧")
    async def email_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.disabled = True
        await interaction.response.send_modal(RegisterModal(self.mailCog, self))


class RegisterModal(disnake.ui.Modal):
    def __init__(self, mailCog, lastView: RegisterView) -> None:
        self.mailCog = mailCog
        self.lastView: RegisterView = lastView
        components = [
            disnake.ui.TextInput(label="Prénom", custom_id="first_name", placeholder="Théodore"),
            disnake.ui.TextInput(label="Nom", custom_id="last_name", placeholder="Verhaegen"),
            disnake.ui.TextInput(label="Addresse mail ULB:", custom_id="email", placeholder="ex : t.verhaegen@ulb.be"),
        ]
        super().__init__(title=title, components=components, timeout=60 * 20)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title=title, description=f"Vérification en cours...", color=disnake.Color.teal()
            ).set_thumbnail(url=Bot.BEP_image),
            view=self.lastView,
        )
        name: str = f"{interaction.text_values.get('first_name')} {interaction.text_values.get('last_name')}"
        email: str = interaction.text_values.get("email")
        if self.mailCog.check_email_validity(email):
            if self.mailCog.check_email_unicity(email):
                token: str = self.mailCog.send_token_mail(email)
                await interaction.edit_original_message(
                    embed=disnake.Embed(
                        title=title,
                        description=f"""Un token à été envoyé à l'addresse mail ***{email}***.""",
                        color=disnake.Color.teal(),
                    )
                    .set_thumbnail(url=Bot.BEP_image)
                    .set_footer(
                        text=f"""Le token est valide pendant {self.mailCog.token_validity_time//60} minutes, tout comme le bouton sous ce message."""
                    ),
                    view=EmailTokenView(self.mailCog, name, email, token),
                )
            else:
                await interaction.edit_original_message(
                    embed=disnake.Embed(
                        title=title,
                        description=f"L'addresse mail ***{email}*** est déjà associée à un autre utilisateur.\nSi c'est bien ton addresse mail et que tu penses que quelqu'un aurait eu accès à ton addresse mail et aurait usurpé ton identité sur ce serveur, contact les administrateurs.",
                        color=disnake.Color.red(),
                    ).set_thumbnail(url=Bot.BEP_image),
                    view=None,
                )
        else:
            self.lastView.email_button.disabled = False
            await interaction.edit_original_message(
                embed=disnake.Embed(
                    title=title,
                    description=f"L'addresse mail **{email}** n'est pas une addresse mail valide.\nL'addresse mail doit être ton addesse mail **ULB**.",
                    color=disnake.Color.dark_orange(),
                ).set_thumbnail(url=Bot.BEP_image),
                view=self.lastView,
            )


class EmailTokenView(disnake.ui.View):
    def __init__(self, mailCog, name: str, email: str, token: str):
        self.mailCog = mailCog
        self.name: str = name
        self.email: str = email
        self.token: str = token
        super().__init__(timeout=None)

    @disnake.ui.button()
    async def token_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.disabled = True
        await interaction.response.send_modal(EmailTokenModal(self.mailCog, self, self.name, self.email, self.token))


class EmailTokenModal(disnake.ui.Modal):
    def __init__(self, mailCog, lastView: EmailTokenView, name: str, email: str, token: str) -> None:
        self.mailCog = mailCog
        self.lastView: EmailTokenView = lastView
        self.name: str = name
        self.email: str = email
        self.token: str = token
        components = [
            disnake.ui.TextInput(
                label=f"Entre ton token de vérification",
                custom_id="token",
                placeholder=f"Token de {self.mailCog.token_size} caractères",
                min_length=self.mailCog.token_size,
                max_length=self.mailCog.token_size,
            )
        ]
        super().__init__(title=title, components=components, timeout=60 * 20)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await interaction.response.edit_message(
            embed=disnake.Embed(
                title=title, description="Vérification en cours...", color=disnake.Color.teal()
            ).set_thumbnail(url=Bot.BEP_image),
            view=self.lastView,
        )
        await asyncio.sleep(2)
        token_submitted: str = interaction.text_values.get("token")
        if token_submitted == self.token:
            if self.mailCog.check_email_unicity(self.email):
                if interaction.user not in self.mailCog.ulb_users.keys():
                    await interaction.edit_original_message(
                        embed=disnake.Embed(
                            title=title,
                            description="Ton addresse mail **ULB** est bien vérifiée !",
                            color=disnake.Color.green(),
                        ).set_thumbnail(url=Bot.BEP_image),
                        view=None,
                    )
                    await self.mailCog.register_user(user=interaction.user, name=self.name, email=self.email)
                else:
                    await interaction.edit_original_message(
                        embed=disnake.Embed(
                            title=title,
                            description=f"Tu as déjà associé l'addresse mail suivante : **{self.mailCog.ulb_users.get(interaction.user).email}**\nSi ce n'est pas ton addresse mail ULB, contact les administrateurs du serveur.",
                            color=disnake.Colour.dark_orange(),
                        ).set_thumbnail(url=Bot.BEP_image),
                        view=None,
                    )
            else:
                await interaction.edit_original_message(
                    embed=disnake.Embed(
                        title=title,
                        description=f"L'addresse mail ***{self.email}*** est déjà associée à un autre utilisateur.\nSi c'est bien ton addresse mail et que tu penses que quelqu'un aurait eu accès à ton addresse mail et aurait usurpé ton identité sur ce serveur, contact les administrateurs.",
                        color=disnake.Color.red(),
                    ).set_thumbnail(url=Bot.BEP_image),
                    view=None,
                )

        else:
            self.lastView.token_button.disabled = False
            await interaction.edit_original_message(
                embed=disnake.Embed(
                    title=title,
                    description="Token invalide ! Essaye à nouveau.",
                    color=disnake.Color.dark_orange(),
                )
                .set_footer(
                    text=f"""Le token est valide pendant {self.mailCog.token_validity_time//60} minutes, tout comme le bouton sous ce message."""
                )
                .set_thumbnail(url=Bot.BEP_image),
                view=self.lastView,
            )


class ForceRegisterModal(RegisterModal):
    def __init__(self, mailCog, user: disnake.User) -> None:
        super().__init__(mailCog, None)
        self.user: disnake.User = user

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        name: str = f"{interaction.text_values.get('first_name')} {interaction.text_values.get('last_name')}"
        email: str = interaction.text_values.get("email")
        await self.mailCog.register_user(user=self.user, name=name, email=email)
        await interaction.response.send_message(
            embed=disnake.Embed(
                description=f"{self.user.mention} à bien été ajouter aux membres de l'ULB !"
            ).set_thumbnail(url=Bot.BEP_image),
            ephemeral=True,
        )
