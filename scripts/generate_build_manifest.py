"""Generate a CI/CD build manifest for the project.

The manifest is safe to commit because it contains repository metadata and file
checksums only. It does not include API keys, account data, or runtime database
content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_INCLUDED_PATHS = (
    ".github/workflows/auto-commit.yml",
    ".github/workflows/ci.yml",
    "api",
    "docs",
    "rainmeter",
    "scripts",
    "tests",
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "pytest.ini",
)


def run_git_command(args: list[str], repo_root: Path) -> str:
    """Run a Git command and return its output.

    Args:
        args: Git arguments after the `git` executable.
        repo_root: Repository root directory.

    Returns:
        Trimmed command output. Returns an empty string when Git is unavailable
        or the command fails.
    """

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""

    return result.stdout.strip()


def calculate_sha256(path: Path) -> str:
    """Calculate a file's SHA-256 checksum.

    Args:
        path: File path to hash.

    Returns:
        Hex-encoded SHA-256 digest.
    """

    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_manifest_files(repo_root: Path, included_paths: tuple[str, ...]) -> list[Path]:
    """Collect files that should be represented in the manifest.

    Args:
        repo_root: Repository root directory.
        included_paths: Relative files or directories to include.

    Returns:
        Sorted list of file paths.
    """

    files: list[Path] = []
    for relative in included_paths:
        path = repo_root / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())

    ignored_parts = {"__pycache__", ".venv", ".test-runtime"}
    ignored_suffixes = {".pyc", ".db", ".log", ".zip"}
    filtered = [
        path
        for path in files
        if not any(part in ignored_parts for part in path.parts)
        and path.suffix.lower() not in ignored_suffixes
        and path.relative_to(repo_root).as_posix() != "docs/build-manifest.json"
    ]
    return sorted(set(filtered), key=lambda item: item.relative_to(repo_root).as_posix())


def build_file_entry(path: Path, repo_root: Path) -> dict[str, Any]:
    """Build one manifest file entry.

    Args:
        path: File path to describe.
        repo_root: Repository root directory.

    Returns:
        Dictionary with relative path, size, and checksum.
    """

    return {
        "path": path.relative_to(repo_root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": calculate_sha256(path),
    }


def build_manifest(repo_root: Path, note: str) -> dict[str, Any]:
    """Build the full manifest payload.

    Args:
        repo_root: Repository root directory.
        note: Human-readable note supplied by the workflow operator.

    Returns:
        Manifest dictionary ready for JSON serialization.
    """

    files = iter_manifest_files(repo_root, DEFAULT_INCLUDED_PATHS)
    return {
        "project": "quant-trading-rainmeter-hud",
        "mode": "monitoring-only",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_branch": run_git_command(["branch", "--show-current"], repo_root),
        "git_commit": run_git_command(["rev-parse", "HEAD"], repo_root),
        "note": note,
        "safety_boundary": {
            "trading_execution": False,
            "private_api_keys": False,
            "order_placement": False,
        },
        "file_count": len(files),
        "files": [build_file_entry(path, repo_root) for path in files],
    }


def write_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    """Write a manifest to disk.

    Args:
        manifest: Manifest dictionary.
        output_path: Destination JSON path.

    Returns:
        None.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(description="Generate the project build manifest.")
    parser.add_argument(
        "--output",
        default="docs/build-manifest.json",
        help="Manifest output path relative to the repository root.",
    )
    parser.add_argument(
        "--note",
        default="Automated CI/CD manifest update.",
        help="Operator note to include in the manifest.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate and write the project build manifest.

    Returns:
        None.
    """

    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / args.output
    write_manifest(build_manifest(repo_root, args.note), output_path)
    print(f"Wrote {output_path.relative_to(repo_root).as_posix()}")


if __name__ == "__main__":
    main()
