import httpx
from typing import List

from mafa.config.settings import Settings


class DiscordNotifier:
    """Simple Discord webhook notifier."""

    def __init__(self, settings: Settings):
        if settings.notification.provider != "discord":
            raise ValueError("DiscordNotifier instantiated but provider is not 'discord'")
        self.webhook_url = settings.notification.discord_webhook_url
        if not self.webhook_url:
            raise ValueError("discord_webhook_url must be set in configuration")

    def _format_listing(self, listing: dict) -> str:
        title = listing.get("title", "N/A")
        price = listing.get("price", "N/A")
        source = listing.get("source", "N/A")
        return f"🏠 {title}\\n💰 {price}\\n📍 {source}"

    def send_listings(self, listings: List[dict]) -> None:
        """Send a message containing all new listings via Discord webhook."""
        if not listings:
            return
        content = "\\n\\n".join(self._format_listing(l) for l in listings)
        payload = {"content": content}
        try:
            httpx.post(self.webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")