# -*- coding: utf-8 -*-
import disnake


class EmailAddressModal(disnake.ui.Modal):
    def __init__(self, mailCog) -> None:
        """Modal for email address form

        Parameters
        ----------
        register_user_func : function
            The function to be called once an email address is verified.

            The function should accept the following keyword argmument: user (`disnake.User`), email (`str`)
        """
        self.mailCog = mailCog
        components = [
            disnake.ui.TextInput(
                label="Addresse mail ULB:", custom_id="email", placeholder="ex : t.verhaegen@ulb.be", min_length=10
            )
        ]
        super().__init__(title="Vérification de l'addresse mail", components=components, timeout=60 * 20)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        await interaction.response.defer(ephemeral=True)
        member: disnake.Member = interaction.author
        email: str = interaction.text_values.get("email")
        if self.mailCog.check_email_validity(email):
            if self.mailCog.check_email_unicity(email):
                token: str = self.mailCog.send_token_mail(email)
                await interaction.edit_original_response(
                    embed=disnake.Embed(
                        title="Vérification de l'addresse mail",
                        description=f"""Un token à été envoyé à l'addresse mail ***{email}***.""",
                        color=disnake.Color.teal(),
                    ).set_footer(
                        text=f"""Le token est valid pendant {self.mailCog.token_validity_time//60} minutes, tout comme le bouton sous ce message."""
                    ),
                    view=EmailTokenView(self.mailCog, member, email, token),
                )
            else:
                await interaction.edit_original_response(
                    embed=disnake.Embed(
                        title="Vérification de l'addresse mail",
                        description=f"L'addresse mail ***{email}*** est déjà associée à un autre utilisateur.\nSi c'est bien ton addresse mail et que tu penses que quelqu'un aurait eu accès à ton addresse mail et aurait usurpé ton identité sur ce serveur, contact les administrateurs.",
                        color=disnake.Color.red(),
                    )
                )
        else:
            await interaction.edit_original_response(
                embed=disnake.Embed(
                    title="Vérification de l'addresse mail",
                    description=f"L'addresse mail **{email}** n'est pas une addresse mail valide.\nL'addresse mail doit être ton addesse mail **ULB**.",
                    color=disnake.Color.dark_orange(),
                )
            )


class EmailTokenView(disnake.ui.View):
    def __init__(self, mailCog, member: disnake.Member, email: str, token: str):
        self.mailCog = mailCog
        self.member: disnake.Member = member
        self.email: str = email
        self.token: str = token
        super().__init__(timeout=None)

    @disnake.ui.button(label="Entrer le token", emoji="📧")
    async def token_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.send_modal(EmailTokenModal(self.mailCog, self.member, self.email, self.token))


class EmailTokenModal(disnake.ui.Modal):
    def __init__(self, mailCog, member: disnake.Member, email: str, token: str) -> None:
        self.mailCog = mailCog
        self.member: disnake.Member = member
        self.email: str = email
        self.token: str = token
        print(self.token)
        components = [
            disnake.ui.TextInput(
                label=f"Entre ton token de vérification",
                custom_id="token",
                placeholder=f"Token de {self.mailCog.token_size} caractères",
                min_length=self.mailCog.token_size,
                max_length=self.mailCog.token_size,
            )
        ]
        super().__init__(title="Vérification de l'addresse mail (2/2)", components=components, timeout=60 * 20)

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        token_submitted: str = interaction.text_values.get("token")
        if token_submitted == self.token:
            if self.mailCog.check_email_unicity(self.email):
                if self.member not in self.mailCog.ulb_users.keys():
                    await interaction.response.edit_message(
                        embed=disnake.Embed(
                            title="Vérification de l'addresse mail",
                            description="Ton addresse mail **ULB** est bien vérifiée !",
                            color=disnake.Color.green(),
                        ),
                        view=None,
                    )
                    await self.mailCog.register_user(member=self.member, email=self.email)
                else:
                    await interaction.response.edit_message(
                        embed=disnake.Embed(
                            title="Vérification de l'addresse mail",
                            description=f"Tu as déjà associé l'addresse mail suivante : **{self.mailCog.ulb_users.get(self.member).email}**\nSi ce n'est pas ton addresse mail ULB, contact les administrateurs du serveur.",
                            color=disnake.Colour.dark_orange(),
                        ),
                        view=None,
                    )
            else:
                await interaction.response.edit_message(
                    embed=disnake.Embed(
                        title="Vérification de l'addresse mail",
                        description=f"L'addresse mail ***{self.email}*** est déjà associée à un autre utilisateur.\nSi c'est bien ton addresse mail et que tu penses que quelqu'un aurait eu accès à ton addresse mail et aurait usurpé ton identité sur ce serveur, contact les administrateurs.",
                        color=disnake.Color.red(),
                    ),
                    view=None,
                )

        else:
            await interaction.response.edit_message(
                embed=disnake.Embed(
                    title="Vérification de l'addresse mail",
                    description="Token invalide !",
                    color=disnake.Color.dark_orange(),
                )
            )
