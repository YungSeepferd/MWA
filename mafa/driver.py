"""
Enhanced Selenium driver helper for MAFA.

Provides a context manager ``SeleniumDriver`` that automatically installs the
appropriate ChromeDriver version via ``webdriver_manager`` and configures a
head‑less Chrome instance with anti-detection measures. The driver is guaranteed
to be quit on exit, preventing orphaned browser processes.
"""

from __future__ import annotations

import logging
import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Generator

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class SeleniumDriverError(Exception):
    """Custom exception for Selenium driver issues."""
    pass


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

    def __init__(self, headless: bool = True, driver_path: Path | None = None,
                 user_agent: str | None = None, timeout: int = 30):
        """
        Parameters
        ----------
        headless: bool, optional
            Run Chrome in head‑less mode (default: True).
        driver_path: Path | None, optional
            If supplied, ``webdriver_manager`` will use this directory to cache the
            driver binary. If ``None`` the default cache location is used.
        user_agent: str | None, optional
            Custom user agent string to avoid detection.
        timeout: int, optional
            Page load timeout in seconds (default: 30).
        """
        self.headless = headless
        self.driver_path = driver_path
        self.user_agent = user_agent
        self.timeout = timeout
        self._driver: webdriver.Chrome | None = None

    def __enter__(self) -> webdriver.Chrome:
        """Initialize Chrome driver with enhanced configuration."""
        try:
            options = webdriver.ChromeOptions()
            
            # Core Chrome options for stability
            if self.headless:
                options.add_argument("--headless=new")  # New headless mode
                options.add_argument("--disable-gpu")
            else:
                options.add_argument("--start-maximized")
            
            # Anti-detection measures
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Performance and stability options
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Faster loading
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")
            
            # Enable JavaScript for dynamic content (required for modern websites)
            # options.add_argument("--disable-javascript")  # Disabled to allow dynamic content
            
            # User agent to avoid detection
            if self.user_agent:
                options.add_argument(f"--user-agent={self.user_agent}")
            else:
                # Use a realistic user agent
                options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")
            
            # Suppress Chrome warnings and info
            prefs = {
                "profile.default_content_setting_values.media_stream_mic": 2,
                "profile.default_content_setting_values.media_stream_camera": 2,
            }
            options.add_experimental_option("prefs", prefs)

            # Resolve driver binary with error handling
            logger.info("Initializing Chrome driver...")
            
            if self.driver_path:
                service = ChromeService(
                    ChromeDriverManager(path=str(self.driver_path)).install()
                )
            else:
                service = ChromeService(ChromeDriverManager().install())

            # Create driver with enhanced options
            self._driver = webdriver.Chrome(service=service, options=options)
            
            # Set page load timeout
            self._driver.set_page_load_timeout(self.timeout)
            
            # Execute script to hide webdriver property
            self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome driver initialized successfully")
            return self._driver
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise SeleniumDriverError(f"Chrome driver initialization failed: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Clean up Chrome driver resources."""
        if self._driver is not None:
            try:
                logger.debug("Closing Chrome driver...")
                self._driver.quit()
                logger.debug("Chrome driver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Chrome driver: {e}")
                # Don't re-raise - cleanup errors shouldn't propagate
                pass
        
        # Don't suppress exceptions that occurred inside the context
        return False