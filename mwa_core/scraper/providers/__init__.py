"""
Scraper providers for MWA Core.

This module contains the base provider protocol and implementations
for different apartment listing websites.
"""

from .base import BaseProvider, Listing
from .immoscout import ImmoScoutProvider
from .wg_gesucht import WgGesuchtProvider

__all__ = ["BaseProvider", "Listing", "ImmoScoutProvider", "WgGesuchtProvider"]