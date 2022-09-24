# -*- coding: utf-8 -*-
""""
Discord bot written in python using disnake library.
Copyright (C) 2022 - Oscar Van Slijpe

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import logging.handlers
import os
import platform
import traceback
import tracemalloc

tracemalloc.start()

import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext.commands import InteractionBot


class Bot(InteractionBot):

    BEP_image = "https://i.imgur.com/BHgic3o.png"

    def __init__(self, logger, logFormatter):
        self.logger = logger
        self.logFormatter = logFormatter
        self.test_mode = bool(os.getenv("TEST"))
        self.start_succed: bool = True
        intents = disnake.Intents.all()  # Allow the use of custom intents

        if self.test_mode:
            logging.info("Starting in test mod...")
            super().__init__(intents=intents, test_guilds=[int(os.getenv("BEP_SERVER"))])
        else:
            logging.info("Starting in prod mod...")
            super().__init__(intents=intents)

        self.load_commands()

    def tracebackEx(self, ex):
        if type(ex) == str:
            return "No valid traceback."
        ex_traceback = ex.__traceback__
        if ex_traceback is None:
            ex_traceback = ex.__traceback__
        tb_lines = [line.rstrip("\n") for line in traceback.format_exception(ex.__class__, ex, ex_traceback)]
        return "".join(tb_lines)

    async def on_ready(self) -> None:
        """
        The code in this even is executed when the bot is ready
        """
        self.log_channel = self.get_channel(int(os.getenv("LOG_CHANNEL")))
        logging.info("-" * 50)
        logging.info("-" * 50)
        logging.info(f"| Logged in as {self.user.name}")
        logging.info(f"| disnake API version: {disnake.__version__}")
        logging.info(f"| Python version: {platform.python_version()}")
        logging.info(f"| Running on: {platform.system()} {platform.release()} ({os.name})")
        logging.info(f"| Owner : {self.owner}")
        logging.info(f"| Cogs loaded : " + ", ".join([f"{cog}" for cog in self.cogs.keys()]))
        logging.info("| Started successfully !" if self.start_succed else "| Started with some issues...")
        logging.info(f"| Ready !")
        logging.info("-" * 50)

    def load_commands(self) -> None:
        for extension in os.listdir(f"./cogs"):
            if extension != ".gitignore":
                try:
                    self.load_extension(f"cogs.{extension}.{extension}")
                    logging.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    logging.warning(f"Failed to load extension {extension}\n{exception}\n{self.tracebackEx(exception)}")
                    self.start_succed = False

    async def send_error_log(self, interaction: ApplicationCommandInteraction, error: Exception):
        tb = self.tracebackEx(error)
        logging.error(
            f"{error} raised on command /{interaction.application_command.name} from {interaction.guild.name} #{interaction.channel.name} by {interaction.author.name}.\n{tb}"
        )
        await interaction.send(
            content=self.owner.mention,
            embed=disnake.Embed(
                title=":x: __**ERROR**__ :x:",
                description=f"Une erreur s'est produite lors de la commande **/{interaction.application_command.name}**\n{self.owner.mention} a été prévenu et corrigera ce bug au plus vite !",
                color=disnake.Colour.red(),
            ),
            delete_after=10,
        )
        await self.log_channel.send(
            embed=disnake.Embed(title=f":x: __** ERROR**__ :x:", description=f"```{error}```").add_field(
                name=f"Raised on command :",
                value=f"**/{interaction.application_command.name}:{interaction.id}** from {interaction.guild.name} #{interaction.channel.mention} by {interaction.author.mention} at {interaction.created_at} with options\n```{interaction.filled_options}```"
                + (f" and target\n``'{interaction.target}``'." if interaction.target else "."),
            )
        )
        n = len(tb) // 4050
        for i in range(n):
            await self.log_channel.send(embed=disnake.Embed(description=f"```python\n{tb[4050*i:4050*(i+1)]}```"))
        await self.log_channel.send(embed=disnake.Embed(description=f"```python\n{tb[4050*n:]}```"))

    async def on_slash_command(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        logging.info(
            f"Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_user_command(self, interaction: disnake.UserCommandInteraction) -> None:
        logging.info(
            f"User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_message_command(self, interaction: disnake.MessageCommandInteraction) -> None:
        logging.info(
            f"Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' started..."
        )

    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: Exception) -> None:
        await self.send_error_log(interaction, error)

    async def on_user_command_error(self, interaction: disnake.UserCommandInteraction, error: Exception) -> None:
        await self.send_error_log(interaction, error)

    async def on_message_command_error(self, interaction: disnake.MessageCommandInteraction, error: Exception) -> None:
        await self.send_error_log(interaction, error)

    async def on_slash_command_completion(self, interaction: disnake.ApplicationCommandInteraction) -> None:
        logging.info(
            f"Slash command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_user_command_completion(self, interaction: disnake.UserCommandInteraction) -> None:
        logging.info(
            f"User command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )

    async def on_message_command_completion(self, interaction: disnake.MessageCommandInteraction) -> None:
        logging.info(
            f"Message command '{interaction.application_command.name}:{interaction.id}' from '{interaction.guild.name+'#'+interaction.channel.name if interaction.guild else 'DM'}' by '{interaction.author.name}' at '{interaction.created_at}' ended normally"
        )
