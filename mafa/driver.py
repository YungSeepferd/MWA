"""
Selenium driver helper for MAFA.

Provides a context manager ``SeleniumDriver`` that automatically installs the
appropriate ChromeDriver version via ``webdriver_manager`` and configures a
head‑less Chrome instance. The driver is guaranteed to be quit on exit,
preventing orphaned browser processes.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from typing import Generator

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumDriver(AbstractContextManager):
    """
    Context manager that yields a ready‑to‑use ``webdriver.Chrome`` instance.

    Example
    -------
    >>> from mafa.driver import SeleniumDriver
    >>> with SeleniumDriver() as driver:
    ...     driver.get("https://example.com")
    ...     # interact with the page
    """

    def __init__(self, headless: bool = True, driver_path: Path | None = None):
        """
        Parameters
        ----------
        headless: bool, optional
            Run Chrome in head‑less mode (default: True).
        driver_path: Path | None, optional
            If supplied, ``webdriver_manager`` will use this directory to cache the
            driver binary. If ``None`` the default cache location is used.
        """
        self.headless = headless
        self.driver_path = driver_path
        self._driver: webdriver.Chrome | None = None

    def __enter__(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
        # Suppress unnecessary logs
        options.add_argument("--log-level=3")
        # Ensure a stable window size for consistent element locations
        options.add_argument("--window-size=1920,1080")

        # Resolve driver binary – webdriver_manager handles version matching
        if self.driver_path:
            service = ChromeService(
                ChromeDriverManager(path=str(self.driver_path)).install()
            )
        else:
            service = ChromeService(ChromeDriverManager().install())

        self._driver = webdriver.Chrome(service=service, options=options)
        return self._driver

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # Always quit the driver, even if an exception occurred.
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                # Swallow any cleanup errors – they are not critical for the caller.
                pass
        # Propagate any exception that happened inside the with‑block.
        return False