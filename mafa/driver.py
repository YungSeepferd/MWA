"""
Enhanced Selenium driver helper for MAFA.

Provides a context manager ``SeleniumDriver`` that automatically installs the
appropriate ChromeDriver version via ``webdriver_manager`` and configures a
head‑less Chrome instance with anti-detection measures. The driver is guaranteed
to be quit on exit, preventing orphaned browser processes.
"""

from __future__ import annotations

import logging
import os
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
            
            try:
                if self.driver_path:
                    driver_path = ChromeDriverManager(path=str(self.driver_path)).install()
                else:
                    driver_path = ChromeDriverManager().install()
                
                # The install() method might return a directory or the wrong file
                # We need to find the actual chromedriver binary
                driver_path_obj = Path(driver_path)
                logger.info(f"WebDriver Manager returned path: {driver_path}")
                logger.info(f"Path type: {'directory' if driver_path_obj.is_dir() else 'file'}")
                
                # If WebDriver Manager returned a file that's not the actual binary, find the correct one
                if driver_path_obj.is_file() and 'THIRD_PARTY_NOTICES' in driver_path_obj.name:
                    # WebDriver Manager returned the wrong file, find the actual binary
                    driver_dir = driver_path_obj.parent
                    logger.info(f"Searching for actual ChromeDriver binary in: {driver_dir}")
                    
                    # Look for the actual chromedriver binary
                    actual_binary_path = driver_dir / "chromedriver"
                    if actual_binary_path.exists() and actual_binary_path.is_file():
                        driver_path = str(actual_binary_path)
                        logger.info(f"Found actual ChromeDriver binary at: {driver_path}")
                    else:
                        # Search for any file that looks like the actual binary
                        for file in driver_dir.iterdir():
                            if file.is_file() and file.name == "chromedriver":
                                driver_path = str(file)
                                logger.info(f"Found ChromeDriver binary at: {driver_path}")
                                break
                        else:
                            # Fallback: use the directory and let the file detection logic handle it
                            driver_path_obj = driver_dir
                
                if driver_path_obj.is_dir():
                    # If it's a directory, look for the chromedriver binary inside
                    # First, try the exact filename "chromedriver" in the root
                    chromedriver_path = driver_path_obj / "chromedriver"
                    if chromedriver_path.exists() and chromedriver_path.is_file():
                        driver_path = str(chromedriver_path)
                        logger.info(f"Found chromedriver at: {driver_path}")
                    else:
                        # If not found, search for the largest executable file named "chromedriver"
                        chromedriver_candidates = []
                        for file in driver_path_obj.rglob("chromedriver"):
                            if file.is_file() and os.access(file, os.X_OK):
                                file_size = file.stat().st_size
                                chromedriver_candidates.append((file, file_size))
                        
                        if chromedriver_candidates:
                            # Select the largest executable file (likely the actual binary)
                            chromedriver_candidates.sort(key=lambda x: x[1], reverse=True)
                            selected_file, file_size = chromedriver_candidates[0]
                            driver_path = str(selected_file)
                            logger.info(f"Found chromedriver (size: {file_size} bytes) at: {driver_path}")
                        else:
                            # Fallback: search for any file that looks like a ChromeDriver binary
                            for file in driver_path_obj.rglob("chromedriver*"):
                                if file.is_file() and not file.name.endswith(('.zip', '.txt', '.chromedriver')):
                                    file_size = file.stat().st_size
                                    is_executable = os.access(file, os.X_OK)
                                    is_large_enough = file_size > 10000000  # At least 10MB for ChromeDriver
                                    is_actual_binary = file_size > 15000000  # ChromeDriver is typically >15MB
                                    
                                    # Prioritize actual binary files
                                    if is_actual_binary and is_executable:
                                        driver_path = str(file)
                                        logger.info(f"Found ChromeDriver binary (size: {file_size} bytes) at: {driver_path}")
                                        break
                                    elif is_large_enough and is_executable:
                                        driver_path = str(file)
                                        logger.info(f"Found potential ChromeDriver (size: {file_size} bytes) at: {driver_path}")
                                        break
                elif driver_path_obj.is_file():
                    # If it's a file but has the wrong name, find the real binary
                    if driver_path_obj.name.endswith(('.chromedriver', '.txt', '.zip')):
                        # Look in the same directory for the actual binary
                        parent_dir = driver_path_obj.parent
                        for file in parent_dir.glob("chromedriver"):
                            if file.is_file() and os.access(file, os.X_OK):
                                driver_path = str(file)
                                logger.info(f"Found chromedriver at: {driver_path}")
                                break
                
                # Final verification
                driver_path_obj = Path(driver_path)
                if not driver_path_obj.exists():
                    raise SeleniumDriverError(f"Chrome driver not found at: {driver_path}")
                
                if not driver_path_obj.is_file():
                    raise SeleniumDriverError(f"Chrome driver path is not a file: {driver_path}")
                
                if not os.access(driver_path_obj, os.X_OK):
                    # Try to make it executable
                    try:
                        driver_path_obj.chmod(0o755)
                        logger.info(f"Made chromedriver executable: {driver_path}")
                    except Exception as e:
                        logger.warning(f"Could not make chromedriver executable: {e}")
                
                # Double-check it's not a text file
                if driver_path_obj.stat().st_size < 10000:
                    raise SeleniumDriverError(f"Chrome driver at {driver_path} is too small to be a binary")
                
                service = ChromeService(str(driver_path_obj))
                
            except Exception as e:
                logger.error(f"Failed to resolve Chrome driver: {e}")
                raise SeleniumDriverError(f"Chrome driver resolution failed: {e}")

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