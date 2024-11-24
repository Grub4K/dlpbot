from __future__ import annotations

import logging
import re

import discord

logger = logging.getLogger(__name__)


class Client(discord.Client):
    def __init__(self, /, channel_ids: list[int] | None = None):
        intents = discord.Intents.default()
        intents.message_content = True

        self.__version_pattern = re.compile(
            r"^\[debug\] yt-dlp version",
            re.MULTILINE,
        )
        self.__config_pattern = re.compile(
            r'^\[debug\] (?:(?:\| )*(?:[^ ]+ config|Config)(?: ".*?")?: |params: {)',
            re.MULTILINE,
        )
        self.__extraction_pattern = re.compile(
            r"^\[[^\]]+\] Extracting URL: ",
            re.MULTILINE,
        )
        self.__channel_ids: list[int] = channel_ids or []
        super().__init__(intents=intents)

    async def on_ready(self, /):
        assert self.user
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message, /):
        if message.author == self.user or message.author.bot:
            return

        if message.channel.id not in self.__channel_ids:
            pass

        content = message.content
        if message.attachments:
            for attachment in message.attachments:
                if self.__is_textfile(attachment):
                    content = (await attachment.read()).decode("latin-1")
                    break

            else:
                if any(map(self.__is_picture, message.attachments)):
                    await message.reply(
                        "found picture, please use a code block",
                        mention_author=True,
                        silent=True,
                    )
                    return

        if self.__version_pattern.search(content):
            if self.__config_pattern.search(content):
                return
            logger.info(f"{message.author}: missing config")
            await message.reply(
                "the log is incomplete please paste the **ENTIRE** log after using `-v`",
                mention_author=True,
                silent=True,
            )
            return

        if not self.__extraction_pattern.search(content):
            logger.info(f"{message.author}: no log at all")
            return

        await message.reply(
            "found a non verbose log, please use `-v`",
            mention_author=True,
            silent=True,
        )

    async def on_message_edit(self, before, after):
        msg = f"{before.author} edited their message:\n{before.content} -> {after.content}"
        logger.info(msg)

    def __is_textfile(self, attachment: discord.Attachment, /):
        if (
            attachment.flags.thumbnail
            or attachment.flags.clip
            or attachment.flags.remix
        ):
            return False

        if attachment.content_type and attachment.content_type.startswith("text/"):
            logger.info(f"attachment: text content type: {attachment}")
            return True

        return False

    def __is_picture(self, attachment: discord.Attachment, /):
        if (
            attachment.flags.thumbnail
            or attachment.flags.clip
            or attachment.flags.remix
        ):
            return False

        if attachment.content_type and attachment.content_type.startswith("image/"):
            logger.info(f"attachment: image content type: {attachment}")
            return True

        if any(
            attachment.filename.endswith(f".{ext}")
            for ext in ["png", "jpg", "jpeg", "webm", "gif"]
        ):
            logger.info(f"attachment: image extension: {attachment}")
            return True

        return False
