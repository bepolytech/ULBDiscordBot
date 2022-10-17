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


def addLoggingLevel(levelName: str, levelNum: int, methodName: str = None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


if __name__ == "__main__":

    addLoggingLevel("TRACE", logging.INFO - 5)

    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.TRACE)
    rootLogger.addHandler(consoleHandler)

    if platform.system() == "Linux":
        fileInfoHandler = logging.handlers.RotatingFileHandler(
            filename="logs/info.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileDebugHandler = logging.handlers.RotatingFileHandler(
            filename="logs/debug.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileInfoHandler.setFormatter(logFormatter)
        fileInfoHandler.setLevel(logging.TRACE)
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
