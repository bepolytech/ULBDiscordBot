# -*- coding: utf-8 -*-
import logging

import disnake

from .utils import remove_user
from classes.database import Database


class YearlyUpdate(disnake.ui.View):
    def __init__(self, reason: str):
        super().__init__()
        self.reason = reason

    @classmethod
    async def new(cls, reason: str, inter: disnake.ApplicationCommandInteraction):
        new_view = cls(reason)
        await inter.response.send_message(
            embed=disnake.Embed(
                title="Yearly-update",
                description="Cette commande va supprimer **TOUS** les utilisateur.rice.s vérifié.e.s et leur envoyer un message leur demandant de vérifier leur adresse email ULB à nouveau.\nCette commande ne devrait etre utilisée uniquement en début de chaque année académique (vers fin Octobre, début Novembre, le temps que les inscriptions se finalisent).\n**Êtes-vous sûr.e de vouloir utiliser cette commande ?**",
                color=disnake.Color.orange(),
            ),
            view=new_view,
        )

    async def remove_and_notify(self, user: disnake.User):
        await remove_user(user)
        await user.send(
            embed=disnake.Embed(
                title="ULB accès retiré",
                description=f"Ta vérification aux serveurs Discord ULB a été retirée pour la raison suivante : *{self.reason}*.\nUtilise **/ulb** pour re-vérifier ton adresse email ULB afin d'avoir à nouveau accès aux serveurs ULB sur Discord.",
            )
        )

    @disnake.ui.button(label="Confirmer", style=disnake.ButtonStyle.danger)
    async def confirm(self, button: disnake.Button, inter: disnake.ApplicationCommandInteraction):
        await inter.response.edit_message(
            embed=disnake.Embed(
                title="Yearly-update", description="Removing and notifiyng all users...", color=disnake.Colour.orange()
            ),
            view=None,
        )
        logging.info("[yearly-update] Starting to remove and notify all users")
        users = list(Database.ulb_users.keys())
        for user in users:
            await self.remove_and_notify(user)
        logging.info("[yearly-update] All users removed and notified !")
        if inter.is_expired():
            await inter.channel.send(
                embed=disnake.Embed(title="Yearly-update", description="Done !", color=disnake.Colour.teal())
            )
        else:
            inter.edit_original_response(
                embed=disnake.Embed(title="Yearly-update", description="Done !", color=disnake.Colour.teal())
            )
