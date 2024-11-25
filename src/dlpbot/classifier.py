from __future__ import annotations

import enum
import logging
import re
import typing

if typing.TYPE_CHECKING:
    import discord

logger = logging.getLogger(__name__)

_VERSION_PATTERN = re.compile(
    r"^\[debug\] yt-dlp version",
    re.MULTILINE,
)
_CONFIG_PATTERN = re.compile(
    r'^\[debug\] (?:(?:\| )*(?:[^ ]+ config|Config)(?: ".*?")?: |params: {)',
    re.MULTILINE,
)
_EXTRACTION_PATTERN = re.compile(
    r"^\[[^\]]+\] Extracting URL: ",
    re.MULTILINE,
)


class Classification(enum.Flag):
    NoLog = 0
    Picture = 1 << 0
    IncompleteLog = 1 << 1
    NonVerboseLog = 1 << 2
    StderrLog = 1 << 3
    VerboseLog = 1 << 4

    def has_verbose(self, /):
        return bool(self & self.VerboseLog)

    def has_non_verbose(self, /):
        return bool(self & self.NonVerboseLog)

    def has_incomplete(self, /):
        return bool(self & self.IncompleteLog)

    def has_stderr(self, /):
        return bool(self & self.StderrLog)

    def has_picture(self, /):
        return bool(self & self.Picture)


async def classify_message(message: discord.Message) -> Classification:
    result = Classification.NoLog

    async for content in _get_text_content(message):
        has_version = _VERSION_PATTERN.search(content)
        has_config = _CONFIG_PATTERN.search(content)
        has_extraction = _EXTRACTION_PATTERN.search(content)

        if has_version and has_config:
            if has_extraction:
                result |= Classification.VerboseLog
            else:
                result |= Classification.StderrLog
            continue

        if has_version:
            assert not has_config, "path checked above"
            if has_extraction:
                result |= Classification.IncompleteLog
            else:
                result |= Classification.StderrLog
            continue

        if has_extraction:
            result |= Classification.NonVerboseLog

    if any(_is_picture(attachment) for attachment in message.attachments):
        result |= Classification.Picture

    return result


async def _get_text_content(message: discord.Message) -> typing.AsyncGenerator[str]:
    yield message.content
    for attachment in filter(_is_textfile, message.attachments):
        yield ((await attachment.read()).decode("latin-1"))


def _is_textfile(attachment: discord.Attachment) -> bool:
    if _is_known_attachment(attachment):
        return False

    if attachment.content_type and attachment.content_type.startswith("text/"):
        logger.info(f"attachment: text content type: {attachment}")
        return True

    return False


def _is_picture(attachment: discord.Attachment) -> bool:
    if _is_known_attachment(attachment):
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


def _is_known_attachment(attachment: discord.Attachment) -> bool:
    return attachment.flags.thumbnail or attachment.flags.clip or attachment.flags.remix
