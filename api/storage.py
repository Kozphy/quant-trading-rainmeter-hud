"""SQLite storage for recent market snapshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def init_db(database_path: Path) -> None:
    """Create the SQLite history table when it is missing.

    Args:
        database_path: Path to the local SQLite database file.

    Returns:
        None.
    """

    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                price_change_percent REAL NOT NULL,
                rsi REAL NOT NULL,
                sma20 REAL NOT NULL,
                sma50 REAL NOT NULL,
                signal TEXT NOT NULL,
                confidence REAL NOT NULL,
                regime TEXT NOT NULL,
                volatility REAL NOT NULL,
                drawdown REAL NOT NULL,
                sharpe REAL NOT NULL,
                exposure REAL NOT NULL,
                bot_status TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_snapshots_symbol_created
            ON market_snapshots(symbol, created_at)
            """
        )
        connection.commit()


def save_market_snapshot(database_path: Path, snapshot: dict[str, Any], bot_status: str, created_at: str) -> None:
    """Persist one market snapshot.

    Args:
        database_path: Path to the SQLite database.
        snapshot: Symbol snapshot produced by the API service layer.
        bot_status: Overall bot status at snapshot time.
        created_at: Local timestamp string for the snapshot.

    Returns:
        None.
    """

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO market_snapshots (
                symbol, price, price_change_percent, rsi, sma20, sma50, signal,
                confidence, regime, volatility, drawdown, sharpe, exposure,
                bot_status, source, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["symbol"],
                snapshot["price"],
                snapshot["price_change_percent"],
                snapshot["rsi"],
                snapshot["sma20"],
                snapshot["sma50"],
                snapshot["signal"],
                snapshot["confidence"],
                snapshot["regime"],
                snapshot["volatility"],
                snapshot["drawdown"],
                snapshot["sharpe"],
                snapshot["exposure"],
                bot_status,
                snapshot["source"],
                created_at,
            ),
        )
        connection.commit()


def prune_history(database_path: Path, symbol: str, keep_limit: int) -> None:
    """Delete older snapshots beyond the configured per-symbol limit.

    Args:
        database_path: Path to the SQLite database.
        symbol: Symbol whose old rows should be removed.
        keep_limit: Maximum number of recent rows to keep.

    Returns:
        None.
    """

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            DELETE FROM market_snapshots
            WHERE symbol = ?
              AND id NOT IN (
                  SELECT id
                  FROM market_snapshots
                  WHERE symbol = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
            """,
            (symbol, symbol, keep_limit),
        )
        connection.commit()


def save_market_snapshots(
    database_path: Path,
    snapshots: list[dict[str, Any]],
    bot_status: str,
    created_at: str,
    keep_limit: int,
) -> None:
    """Persist and prune a batch of market snapshots.

    Args:
        database_path: Path to the SQLite database.
        snapshots: Symbol snapshots produced by the API service layer.
        bot_status: Overall bot status at snapshot time.
        created_at: Local timestamp string for the batch.
        keep_limit: Maximum number of rows to keep for each symbol.

    Returns:
        None.
    """

    init_db(database_path)
    for snapshot in snapshots:
        save_market_snapshot(database_path, snapshot, bot_status, created_at)
        prune_history(database_path, snapshot["symbol"], keep_limit)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row into a plain dictionary.

    Args:
        row: SQLite row from the history query.

    Returns:
        Dictionary representation of the row.
    """

    return {key: row[key] for key in row.keys()}


def get_symbol_history(database_path: Path, symbol: str, limit: int) -> list[dict[str, Any]]:
    """Load recent history rows for one symbol.

    Args:
        database_path: Path to the SQLite database.
        symbol: Symbol to query.
        limit: Maximum number of recent rows to return.

    Returns:
        List of history rows ordered from oldest to newest.
    """

    init_db(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT symbol, price, price_change_percent, rsi, sma20, sma50,
                   signal, confidence, regime, volatility, drawdown, sharpe,
                   exposure, bot_status, source, created_at
            FROM market_snapshots
            WHERE symbol = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()

    return [row_to_dict(row) for row in reversed(rows)]
