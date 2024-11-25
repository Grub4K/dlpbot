from __future__ import annotations

import collections
import logging

import discord

import dlpbot.classifier

logger = logging.getLogger(__name__)


class Client(discord.Client):
    def __init__(self, channel_ids: list[int] | None = None, /):
        intents = discord.Intents.default()
        intents.message_content = True

        self.__channel_ids: list[int] = channel_ids or []
        self.__bad_messages: collections.deque[int] = collections.deque(maxlen=100)
        super().__init__(intents=intents)

    async def on_ready(self, /):
        assert self.user
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message, /):
        if message.author == self.user or message.author.bot:
            return

        if message.channel.id not in self.__channel_ids:
            pass

        await self.__handle_message(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message, /):
        if before.id not in self.__bad_messages:
            return

        logger.info(f"edited message by {after.author!r}]")
        await self.__handle_message(after)

    async def __handle_message(self, message: discord.Message, /):
        classification = await dlpbot.classifier.classify_message(message)
        if message.id in self.__bad_messages:
            self.__bad_messages.remove(message.id)

        if classification is dlpbot.classifier.Classification.NoLog:
            return

        logger.info(f"{classification.name} sent by {message.author!r}")
        if classification.has_verbose():
            return

        self.__bad_messages.append(message.id)
        if classification.has_non_verbose():
            await message.reply(
                "found non verbose log: please use `-v`",
                mention_author=True,
                silent=True,
            )
            return

        if classification.has_incomplete():
            await message.reply(
                "found incomplete log: please paste the **ENTIRE** log after using `-v`",
                mention_author=True,
                silent=True,
            )
            return

        if classification.has_stderr():
            await message.reply(
                "found stderr log: please send both the stdout and stderr logs",
                mention_author=True,
                silent=True,
            )
            return

        if classification.has_picture():
            await message.reply(
                "found picture log: please use a code block with `-v` instead",
                mention_author=True,
                silent=True,
            )
            return
