# -*- coding: utf-8 -*-
from disnake.ext import commands

from bot import Bot


# TODO:
# - Reload google sheet
# - Update all guilds
# - Add users without email verification
# - Change user name
# - Remove user


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        """Initialize the cog"""
        self.bot: Bot = bot


def setup(bot: commands.InteractionBot):
    bot.add_cog(Admin(bot))
