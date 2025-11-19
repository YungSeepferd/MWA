"""
Orchestrator for MAFA.

Coordinates configuration loading, crawling, persistence and (future) notification.
"""

from __future__ import annotations

import re
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional

from loguru import logger
from typing import List

from mafa.config.settings import Settings
from mafa.providers import build_providers
from mafa.notifier.discord import DiscordNotifier
from mafa.db.manager import ListingRepository
from mafa.monitoring import get_metrics_collector, get_health_checker, PerformanceOptimizer
from mafa.exceptions import (
    ConfigurationError,
    ScrapingError,
    DatabaseError,
    NotificationError
)

# Configure loguru with comprehensive logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)
logger.add(
    "logs/mafa_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    rotation="1 day",
    retention="30 days"
)


def _price_to_int(price_str: str) -> int:
    """
    Convert a price string like \"1.200 €\" or \"€1.200\" to an integer number of euros.
    Non‑numeric characters are stripped; commas and periods are treated as thousand
    separators. Returns 0 if conversion fails.
    """
    # Remove any non‑digit characters (including currency symbols, spaces, etc.)
    cleaned = re.sub(r"[^\d]", "", price_str)
    try:
        return int(cleaned) if cleaned else 0
    except ValueError:
        logger.warning(f"Failed to convert price string to int: {price_str}")
        return 0


def _filter_listings(listings: list[dict], criteria: Settings.search_criteria) -> list[dict]:
    """
    Filter listings according to the user's search criteria.

    - ``max_price``: keep listings with a price <= max_price.
    - ``zip_codes``: keep listings whose title contains any of the zip codes.
    - ``min_rooms``: not implemented here because the source does not expose room count.
    """
    filtered = []
    logger.debug(f"Filtering {len(listings)} listings with criteria: max_price={criteria.max_price}, zip_codes={criteria.zip_codes}")
    
    for listing in listings:
        try:
            price = _price_to_int(listing.get("price", ""))
            if price > criteria.max_price:
                continue
            
            # Simple zip‑code check: look for any zip code substring in the title.
            title = listing.get("title", "")
            if any(zip_code in title for zip_code in criteria.zip_codes):
                filtered.append(listing)
        except Exception as e:
            logger.error(f"Error filtering listing: {listing.get('title', 'unknown')}, error: {e}")
            continue
    
    logger.info(f"Filtered {len(filtered)} listings matching criteria from {len(listings)} total")
    return filtered


def _validate_listing_data(listing: dict) -> bool:
    """Validate that a listing has required fields."""
    required_fields = ["title", "price", "source", "timestamp"]
    return all(field in listing and listing[field] for field in required_fields)


def run(config_path: Path | None = None) -> None:
    """
    Entry point for the MAFA orchestrator.

    Parameters
    ----------
    config_path : Path | None
        Optional path to a custom ``config.json`` file. If omitted the default
        location ``config.json`` (or ``config.example.json`` as a fallback) is used.
    """
    start_time = time.time()
    logger.info("Starting MAFA orchestrator run...")
    
    # Initialize monitoring
    metrics_collector = get_metrics_collector()
    health_checker = get_health_checker(config_path=config_path)
    
    # Perform initial health check
    health_status = health_checker.get_health_status()
    logger.info(f"System health status: {health_status.status}")
    
    if health_status.status == "unhealthy":
        logger.warning(f"System is unhealthy: {', '.join(health_status.issues)}")
        # Continue anyway, but log the issues
    
    try:
        # Load settings – the Settings class handles validation and fallback.
        try:
            settings = Settings.load(path=Path(config_path) if config_path else None)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")

        # Initialise the SQLite repository.
        try:
            repo = ListingRepository()
            logger.info("Database repository initialized")
            
            # Optimize database performance
            db_path = repo.db_path
            PerformanceOptimizer.create_database_indexes(db_path)
            PerformanceOptimizer.optimize_database(db_path)
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

        # Build provider instances based on config and run them.
        all_listings: List[dict] = []
        provider_errors = []
        
        try:
            providers = build_providers(settings.scrapers, config=settings)
            logger.info(f"Built {len(providers)} providers: {[p.__class__.__name__ for p in providers]}")
        except Exception as e:
            logger.error(f"Failed to build providers: {e}")
            raise ConfigurationError(f"Provider configuration invalid: {e}")

        # Scrape listings from each provider
        for provider in providers:
            provider_name = provider.__class__.__name__
            provider_start = time.time()
            logger.info(f"Starting scrape for {provider_name}")
            
            try:
                provider_listings = provider.scrape()
                provider_duration = time.time() - provider_start
                
                # Record metrics
                metrics_collector.record_scrape_attempt(
                    duration=provider_duration,
                    success=True,
                    listings_found=len(provider_listings),
                    new_listings=0  # Will be updated after database insertion
                )
                
                # Validate and filter listings
                valid_listings = [l for l in provider_listings if _validate_listing_data(l)]
                invalid_count = len(provider_listings) - len(valid_listings)
                
                if invalid_count > 0:
                    logger.warning(f"{provider_name}: {invalid_count} invalid listings filtered out")
                
                all_listings.extend(valid_listings)
                logger.info(f"{provider_name}: Scraped {len(valid_listings)} valid listings in {provider_duration:.2f}s")
                
            except Exception as e:
                provider_duration = time.time() - provider_start
                error_msg = f"Failed to scrape {provider_name}: {e}"
                logger.error(error_msg)
                provider_errors.append(error_msg)
                
                # Record failed scrape attempt
                metrics_collector.record_scrape_attempt(
                    duration=provider_duration,
                    success=False,
                    listings_found=0,
                    new_listings=0
                )
                
                # Continue with other providers even if one fails
        
        logger.info(f"Total scraped listings: {len(all_listings)} from {len(providers)} providers")
        
        if not all_listings:
            if provider_errors:
                logger.warning(f"All providers failed. Errors: {'; '.join(provider_errors)}")
            else:
                logger.info("No listings found from any provider")
            
            # Record final metrics for this run
            metrics_collector.record_scrape_attempt(
                duration=time.time() - start_time,
                success=len(provider_errors) == 0,
                listings_found=0,
                new_listings=0
            )
            return

        # Persist new listings, skipping duplicates.
        try:
            new_count = repo.bulk_add(all_listings)
            logger.info(f"Persisted {new_count} new listings (out of {len(all_listings)} total)")
        except Exception as e:
            logger.error(f"Failed to persist listings to database: {e}")
            raise DatabaseError(f"Database persistence failed: {e}")

        # Filter listings according to the user's search criteria.
        try:
            matching = _filter_listings(all_listings, settings.search_criteria)
            logger.info(f"Found {len(matching)} listings matching search criteria")
        except Exception as e:
            logger.error(f"Failed to filter listings: {e}")
            raise ConfigurationError(f"Search criteria filtering failed: {e}")

        # Initialize notifier (Discord) – will be used after CSV generation.
        notifier = None
        try:
            notifier = DiscordNotifier(settings)
            logger.info("Discord notifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Discord notifier: {e}")
            # Continue without notifier - not a critical error

        # Generate a simple CSV report for the matching listings.
        if matching:
            import csv
            from datetime import datetime
            try:
                data_dir = Path(__file__).resolve().parents[3] / "data"
                data_dir.mkdir(exist_ok=True)
                report_path = data_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(report_path, mode="w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = ["title", "price", "source", "timestamp"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for listing in matching:
                        writer.writerow({
                            "title": listing.get("title", ""),
                            "price": listing.get("price", ""),
                            "source": listing.get("source", ""),
                            "timestamp": listing.get("timestamp", "")
                        })
                logger.info(f"Generated CSV report with {len(matching)} listings at {report_path}")
            except Exception as e:
                logger.error(f"Failed to write CSV report: {e}")
                # Continue execution even if CSV generation fails
            
            # Send Discord notifications if possible.
            if notifier:
                try:
                    notifier.send_listings(matching)
                    logger.info(f"Sent Discord notification with {len(matching)} listings")
                except Exception as e:
                    logger.error(f"Failed to send Discord notification: {e}")
                    # Don't raise - notification failure shouldn't crash the application
        else:
            logger.info("No new listings matched the search criteria")
        
        # Log summary
        duration = time.time() - start_time
        logger.info(f"Orchestrator run completed successfully in {duration:.2f}s")
        
        # Update metrics with new listings count
        if all_listings:
            # Re-record with correct new listings count
            metrics_collector.record_scrape_attempt(
                duration=duration,
                success=True,
                listings_found=len(all_listings),
                new_listings=new_count
            )
        
    except (ConfigurationError, DatabaseError, ScrapingError) as e:
        logger.error(f"Application error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise MAFAError(f"Unexpected error during execution: {e}")