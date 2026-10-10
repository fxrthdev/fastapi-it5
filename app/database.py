"""SQLite connection and table setup."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATABASE_FILE = Path(__file__).resolve().parent.parent / "expenses.db"


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    """Open a database connection and always close it after the operation."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    try:
        # Enable Foreign Keys in SQLite
        connection.execute("PRAGMA foreign_keys = ON;")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create users and expenses tables with relationship integrity."""
    with database_connection() as connection:
        # Table 1: Users (contains budget information)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                monthly_budget REAL NOT NULL CHECK (monthly_budget >= 0)
            )
            """
        )

        # Table 2: Expenses (Foreign Key points to users.id)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )