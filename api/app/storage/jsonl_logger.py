"""Safe append-only JSONL logging utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlLogger:
    """Append JSON dictionaries to a .jsonl file without raising write errors."""

    def __init__(self, path: Path) -> None:
        """Initialize a JSONL logger.

        Args:
            path: Output JSONL file path.
        """

        self.path = path

    def append(self, payload: dict[str, Any]) -> None:
        """Append one JSON object as a line.

        Args:
            payload: JSON-serializable dictionary.

        Returns:
            None.
        """

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except OSError:
            return

