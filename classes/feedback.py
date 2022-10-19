# -*- coding: utf-8 -*-
import logging
from typing import List

import disnake

from bot import Bot


class FeedbackType:
    issu = "problème"
    improve = "amélioration"


class FeedbackModal(disnake.ui.Modal):
    def __init__(self, bot: Bot, type: FeedbackType) -> None:
        self.bot: Bot = bot
        self.type: FeedbackType = type
        components: List[disnake.ui.TextInput] = None
        if type == FeedbackType.issu:
            components = [
                disnake.ui.TextInput(
                    label="Problème",
                    placeholder="Quel est le problème que vous avez rencontré",
                    style=disnake.TextInputStyle.paragraph,
                    custom_id="feedback",
                )
            ]
        elif type == FeedbackType.improve:
            components = [
                disnake.ui.TextInput(
                    label="Amélioration",
                    placeholder="Qu'est-ce que vous voudriez améliorer ?",
                    style=disnake.TextInputStyle.paragraph,
                    custom_id="feedback",
                )
            ]
        else:
            raise TypeError("arg 'type' should be a 'FeedbackType'.")
        super().__init__(title="Ulb registration - Feedback", components=components)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        await interaction.response.defer(with_message=True, ephemeral=True)
        logging.trace(f"[Feedback] Returning {self.type} feedback by {interaction.author} from {interaction.guild}")
        feedback: str = interaction.text_values.get("feedback")
        if self.type == FeedbackType.issu:
            embed = disnake.Embed(
                title="Feedback - Problème",
                description="> " + "\n> ".join(feedback.splitlines()),
                color=disnake.Color.red(),
            )
        elif self.type == FeedbackType.improve:
            embed = disnake.Embed(
                title="Feedback - Amélioration",
                description="> " + "\n> ".join(feedback.splitlines()),
                color=disnake.Color.teal(),
            )
        embed.add_field(
            name="**__Origine__**",
            value=f"**User :** {interaction.author}\n**Server :** {interaction.guild}\n**Date :** {interaction.created_at.isoformat()}",
        )
        await self.bot.log_channel.send(embed=embed)
        await interaction.edit_original_response(
            embed=disnake.Embed(
                title="Feedback",
                description="Merci beaucoup pour votre feedback !\nCelui-ci a bien été envoyé et sera pris en compte.",
                color=disnake.Color.blue(),
            )
        )
        logging.trace(f"[Feedback] feedback {self.type} by {interaction.author} from {interaction.guild} ended")
