import httpx
from typing import List

from mafa.config.settings import Settings
from mafa.templates import render_template


class DiscordNotifier:
    """Discord webhook notifier with templated messages."""

    def __init__(self, settings: Settings):
        if settings.notification.provider != "discord":
            raise ValueError("DiscordNotifier instantiated but provider is not 'discord'")
        self.webhook_url = settings.notification.discord_webhook_url
        self.settings = settings
        if not self.webhook_url:
            raise ValueError("discord_webhook_url must be set in configuration")

    def send_listings(self, listings: List[dict], template_name: str = "apply_short.jinja2") -> None:
        """Send templated application messages via Discord webhook."""
        if not listings:
            return
        combined_content = ""
        for listing in listings:
            rendered = render_template(template_name, listing, self.settings)
            combined_content += rendered + "\\n\\n---\\n\\n"
        payload = {"content": combined_content}
        try:
            httpx.post(self.webhook_url, json=payload, timeout=10)
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")