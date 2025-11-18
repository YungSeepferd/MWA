"""
SQLite persistence layer for MAFA.

Provides a ``ListingRepository`` class that creates a ``listings`` table
(if it does not exist) and offers methods to insert new listings while
preventing duplicates via a SHA‑256 hash of the listing content.
"""

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Dict, List

# Ensure the data directory exists – the repository expects ``./data`` at the project root.
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = DATA_DIR / "listings.db"


def _hash_listing(listing: Dict) -> str:
    """
    Compute a stable SHA‑256 hash for a listing dictionary.

    The hash is based on the concatenation of title, price, source and timestamp.
    """
    hash_input = (
        f"{listing.get('title','')}"
        f"{listing.get('price','')}"
        f"{listing.get('source','')}"
        f"{listing.get('timestamp','')}"
    ).encode("utf-8")
    return hashlib.sha256(hash_input).hexdigest()


class ListingRepository:
    """
    Simple repository for storing and querying listings.

    The underlying table schema:

    .. code-block:: sql

        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE
        );
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    price TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    hash TEXT NOT NULL UNIQUE
                );
                """
            )
            conn.commit()

    def add_listing(self, listing: Dict) -> bool:
        """
        Insert a listing if it does not already exist.

        Returns ``True`` if the listing was inserted, ``False`` if it was a duplicate.
        """
        listing_hash = _hash_listing(listing)
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO listings (title, price, source, timestamp, hash)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (
                        listing.get("title"),
                        listing.get("price"),
                        listing.get("source"),
                        listing.get("timestamp"),
                        listing_hash,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Duplicate (hash already present)
                return False

    def listing_exists(self, listing: Dict) -> bool:
        """
        Check whether a listing already exists in the database.
        """
        listing_hash = _hash_listing(listing)
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM listings WHERE hash = ? LIMIT 1;", (listing_hash,)
            )
            return cur.fetchone() is not None

    def bulk_add(self, listings: List[Dict]) -> int:
        """
        Insert multiple listings, skipping duplicates.

        Returns the number of newly inserted rows.
        """
        inserted = 0
        with self._connect() as conn:
            for listing in listings:
                listing_hash = _hash_listing(listing)
                try:
                    conn.execute(
                        """
                        INSERT INTO listings (title, price, source, timestamp, hash)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        (
                            listing.get("title"),
                            listing.get("price"),
                            listing.get("source"),
                            listing.get("timestamp"),
                            listing_hash,
                        ),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    continue
            conn.commit()
        return inserted