"""CLI helper that targets the OpenAI backend explicitly."""
from __future__ import annotations

from scripts.run_generator import main


def cli() -> int:
    return main()


if __name__ == "__main__":
    raise SystemExit(cli())
