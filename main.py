"""Backward-compatible project entry point for CLI, ingestion, and FastAPI."""

import argparse
import asyncio

from app.api.main import app
from app.cli import start_cli
from app.ingest import main as ingest


def main() -> None:
    parser = argparse.ArgumentParser(description="FirstAidOps")
    parser.add_argument(
        "command", nargs="?", choices=["cli", "ingest"], default="cli"
    )
    args = parser.parse_args()
    if args.command == "ingest":
        ingest()
    else:
        asyncio.run(start_cli())


if __name__ == "__main__":
    main()
