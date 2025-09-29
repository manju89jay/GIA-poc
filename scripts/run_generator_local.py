"""CLI helper that targets a locally hosted llama.cpp checkpoint."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.run_generator import main
else:  # pragma: no cover - import guard is runtime dependent
    from .run_generator import main

DEFAULT_MODEL_PATH = Path.home() / ".llama" / "checkpoints" / "Llama-4-Scout-17B-16E-Instruct"


def _preflight(args: argparse.Namespace) -> None:
    if args.backend and args.backend not in {"local", "local-llama", "llama"}:
        raise RuntimeError("run_generator_local.py only supports the local-llama backend")
    args.backend = "local-llama"
    model_path = args.model or os.getenv("LLAMA_MODEL_PATH") or str(DEFAULT_MODEL_PATH)
    resolved = Path(model_path).expanduser()
    if resolved.is_dir():
        ggufs = sorted(resolved.glob("*.gguf"))
        if not ggufs:
            raise RuntimeError(
                "no GGUF checkpoints found in directory. Point --model to the .gguf file"
                f" inside {resolved}."
            )
        resolved = ggufs[0]
    elif not resolved.exists():
        raise RuntimeError(
            "local model checkpoint not found. Set --model or LLAMA_MODEL_PATH to the GGUF file"
            f" (expected at {resolved})."
        )
    try:
        import llama_cpp  # noqa: F401
    except ImportError as exc:  # pragma: no cover - import error surfaces to user
        raise RuntimeError(
            "llama-cpp-python is not installed. Install it with `pip install llama-cpp-python`."
        ) from exc
    args.model = str(resolved)


def cli() -> int:
    return main(
        default_backend="local-llama",
        default_model=str(DEFAULT_MODEL_PATH),
        preflight=_preflight,
    )


if __name__ == "__main__":
    raise SystemExit(cli())
