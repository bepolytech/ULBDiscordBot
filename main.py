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
import logging
import os
import platform

from dotenv import load_dotenv

from bot import Bot

if __name__ == "__main__":

    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)

    if platform.system() == "Linux":
        fileInfoHandler = logging.handlers.RotatingFileHandler(
            filename="logs/info.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileDebugHandler = logging.handlers.RotatingFileHandler(
            filename="logs/debug.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileInfoHandler.setFormatter(logFormatter)
        fileInfoHandler.setLevel(logging.INFO)
        fileInfoHandler.doRollover()
        rootLogger.addHandler(fileInfoHandler)
        fileDebugHandler.setFormatter(logFormatter)
        fileDebugHandler.setLevel(logging.DEBUG)
        fileDebugHandler.doRollover()
        rootLogger.addHandler(fileDebugHandler)

    else:
        logging.warning("Non Linux system. Log info and debug file won't be available.")

    load_dotenv()

    bot = Bot(logger=rootLogger, logFormatter=logFormatter)

    bot.run(os.getenv("DISCORD_TOKEN"))
