"""
Telegram notifier for MAFA.

Uses ``python-telegram-bot`` to send a simple text message to a configured
chat. The bot token and chat ID are read from the ``Settings.notification``
section, which is validated by the ``Settings`` pydantic model.
"""

from __future__ import annotations

from typing import List

from telegram import Bot
from telegram.error import TelegramError

from mafa.config.settings import Settings


class TelegramNotifier:
    """
    Minimal wrapper around ``python-telegram-bot`` that sends a message
    containing a list of new listings.

    Parameters
    ----------
    settings : Settings
        The validated configuration object. ``settings.notification`` must
        contain ``telegram_bot_token`` and ``telegram_chat_id``.
    """

    def __init__(self, settings: Settings):
        self.bot_token = settings.notification.telegram_bot_token
        self.chat_id = settings.notification.telegram_chat_id
        self.bot = Bot(token=self.bot_token)

    def _format_listing(self, listing: dict) -> str:
        """
        Convert a single listing dictionary into a human‑readable string.
        """
        title = listing.get("title", "N/A")
        price = listing.get("price", "N/A")
        source = listing.get("source", "N/A")
        return f"🏠 {title}\\n💰 {price}\\n📍 {source}"

    def send_listings(self, listings: List[dict]) -> None:
        """
        Send a message containing all new listings. If the list is empty,
        nothing is sent.

        The message is built by joining the formatted listings with a blank line.
        """
        if not listings:
            return

        message = "\\n\\n".join(self._format_listing(l) for l in listings)

        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
        except TelegramError as e:
            # In a real application you would log this error.
            print(f"Failed to send Telegram notification: {e}")