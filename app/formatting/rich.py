"""Rich formatting + the forward-signature footer.

Two responsibilities live here:

1. **Signature footer** — the thing the customer specifically asked for.
   Telegram does NOT let a bot inject text *during* a forward: forwarding copies
   a message verbatim and Telegram only adds its own non-customisable
   "Forwarded from <Bot>" header at the *top*. The reliable way to guarantee a
   custom signature *at the bottom* is to BAKE the footer into the text/caption
   of every delivered message. A caption travels with the audio/PDF when it is
   forwarded, so the recipient always sees where it came from — plus a deep link
   back into the bot.

2. **Rich text** — we render the UI with the fully-supported rich entities
   (expandable blockquote, spoiler, bold, custom emoji) via HTML parse mode.
   ``send_text`` additionally tries the Bot API 10.1 ``sendRichMessage`` method
   when ``USE_RICH_MESSAGES`` is enabled, and transparently falls back to HTML.
"""

from __future__ import annotations

import logging
from html import escape

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, Message

from app.config import settings
from app.i18n import t

log = logging.getLogger(__name__)

# Thin separator drawn above the signature footer (em dashes).
_SEPARATOR = "—" * 14

# Captions are capped at 1024 chars by Telegram; keep our text well under it.
CAPTION_LIMIT = 1024


# --------------------------------------------------------------------------- #
#  Deep links & signature footer
# --------------------------------------------------------------------------- #
def deep_link(bot_username: str, payload: str | None = None) -> str:
    """Build a t.me deep link, optionally with a /start payload."""
    base = f"https://t.me/{bot_username}"
    return f"{base}?start={payload}" if payload else base


def signature(lang: str, bot_username: str, payload: str | None = None) -> str:
    """The footer block, prefixed with a blank line + separator."""
    url = deep_link(bot_username, payload)
    link_html = f'<a href="{url}">@{escape(bot_username)}</a>'
    body = t(lang, "sig_text", brand=escape(settings.brand_name), link=link_html)
    return f"\n\n{_SEPARATOR}\n{body}"


def with_signature(
    text: str, lang: str, bot_username: str, payload: str | None = None
) -> str:
    """Append the signature to a normal text message."""
    return f"{text}{signature(lang, bot_username, payload)}"


def _safe_html_prefix(text: str) -> str:
    """Trim a trailing partial HTML tag (``<...``) or entity (``&...``).

    Prevents a length-based cut from landing inside ``<b>`` or ``&amp;`` and
    producing markup Telegram rejects with HTTP 400.
    """
    if text.rfind("<") > text.rfind(">"):
        text = text[: text.rfind("<")]
    if text.rfind("&") > text.rfind(";"):
        text = text[: text.rfind("&")]
    return text.rstrip()


def caption_with_signature(
    caption: str, lang: str, bot_username: str, payload: str | None = None
) -> str:
    """Append the signature to a media caption, trimming to the caption limit.

    Callers already clip raw fields so this rarely truncates; when it must, it
    cuts on a tag/entity-safe boundary rather than mid-markup.
    """
    full = with_signature(caption, lang, bot_username, payload)
    if len(full) <= CAPTION_LIMIT:
        return full
    # Reserve room for the footer; trim the body text, not the signature.
    foot = signature(lang, bot_username, payload)
    keep = max(CAPTION_LIMIT - len(foot) - 1, 0)
    body = _safe_html_prefix(caption[:keep])
    return f"{body}{foot}"


# --------------------------------------------------------------------------- #
#  Bot API 10.1 "Rich Messages" — experimental, flag-gated, with HTML fallback
# --------------------------------------------------------------------------- #
# sendRichMessage shipped on 2026-06-11. Client-library wrappers and the exact
# parameter schema are still stabilising, so this path is OFF by default and
# ALWAYS falls back to HTML rich entities. Confirm the live schema against
# https://core.telegram.org/bots/api#sendrichmessage before enabling.
try:
    from aiogram.methods.base import TelegramMethod

    class SendRichMessage(TelegramMethod[Message]):  # type: ignore[misc]
        __returning__ = Message
        __api_method__ = "sendRichMessage"

        chat_id: int | str
        rich_markdown: str  # GitHub-flavoured Markdown + inline HTML tags
        reply_markup: InlineKeyboardMarkup | None = None
        protect_content: bool | None = None

except Exception:  # pragma: no cover - guards against aiogram internal changes
    SendRichMessage = None  # type: ignore[assignment]


async def send_text(
    bot: Bot,
    chat_id: int,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    disable_web_page_preview: bool = True,
) -> Message:
    """Send a text message, preferring Rich Messages when enabled.

    The HTML path is the dependable default; the rich path is best-effort.
    """
    if settings.use_rich_messages and SendRichMessage is not None:
        try:
            return await bot(
                SendRichMessage(
                    chat_id=chat_id,
                    rich_markdown=text,
                    reply_markup=reply_markup,
                    protect_content=settings.protect_content or None,
                )
            )
        except Exception as exc:  # noqa: BLE001 - fall back on ANY failure
            log.warning("sendRichMessage failed, falling back to HTML: %s", exc)

    return await bot.send_message(
        chat_id,
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
        protect_content=settings.protect_content,
        link_preview_options={"is_disabled": disable_web_page_preview},
    )
