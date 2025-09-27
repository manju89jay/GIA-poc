"""CLI helper for calling the /generate endpoint locally.

The module exposes reusable helpers that our test-suite imports so the
happy-path test mirrors the behaviour of the command-line tool.  Keeping
both code paths in sync guarantees that local invocations and automated
checks operate on the exact same payload and response expectations.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable

import requests

DEFAULT_API_URL = "http://localhost:8000/generate"


def build_payload(
    *,
    root: str,
    old_header_path: Path | str,
    new_header_path: Path | str,
    backend: str = "openai",
    return_zip: bool = True,
    model: str | None = None,
    temperature: float | None = None,
) -> Dict[str, Any]:
    """Create the JSON payload expected by the generator service.

    Parameters mirror the API schema and allow tests as well as the CLI to
    share the exact same request body.  Paths are resolved relative to the
    current working directory so the command works on every platform.
    """

    old_header_text = Path(old_header_path).expanduser().resolve().read_text()
    new_header_text = Path(new_header_path).expanduser().resolve().read_text()
    payload: Dict[str, Any] = {
        "root": root,
        "old_header": old_header_text,
        "new_header": new_header_text,
        "backend": backend,
        "return_zip": return_zip,
    }
    if model is not None:
        payload["model"] = model
    if temperature is not None:
        payload["temperature"] = temperature
    return payload


def call_generator(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the generator endpoint and return the parsed JSON body."""

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def format_response_summary(data: Dict[str, Any]) -> Iterable[str]:
    """Yield human-readable lines that describe the generator result."""

    root = data.get("root", "<unknown>")
    files = data.get("files", []) or []
    yield f"Root: {root}"
    if not files:
        yield "No files returned"
        return
    yield "Files:"
    for entry in files:
        name = entry.get("name", "<unnamed>")
        size = len(entry.get("content", ""))
        yield f"  - {name} ({size} bytes of content)"
    if data.get("zip_base64"):
        yield "Zip archive: present"
    else:
        yield "Zip archive: not requested"


def _warn_missing_openai_key(backend: str) -> None:
    if backend == "openai" and not os.getenv("OPENAI_API_KEY"):
        print(
            "[warning] OPENAI_API_KEY is not set; the FastAPI server will reject",
            "requests when the OpenAI backend is selected.",
        )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call the local GIA generator")
    parser.add_argument(
        "--url",
        default=DEFAULT_API_URL,
        help=f"Generator endpoint URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--root",
        default="ExamplePort",
        help="Root struct name to seed the adapter generation",
    )
    parser.add_argument(
        "--old-header",
        default=str(Path("tests/fixtures/old_header.h")),
        help="Path to the legacy header file",
    )
    parser.add_argument(
        "--new-header",
        default=str(Path("tests/fixtures/new_header.h")),
        help="Path to the updated header file",
    )
    parser.add_argument(
        "--backend",
        default="openai",
        help="LLM backend identifier (default: openai)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override passed to the backend",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Optional sampling temperature passed to the backend",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip requesting the base64 zip payload in the response",
    )
    parser.add_argument(
        "--dump-json",
        type=Path,
        default=None,
        help="Optional file to write the raw JSON response to",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    _warn_missing_openai_key(args.backend)

    payload = build_payload(
        root=args.root,
        old_header_path=args.old_header,
        new_header_path=args.new_header,
        backend=args.backend,
        return_zip=not args.no_zip,
        model=args.model,
        temperature=args.temperature,
    )
    data = call_generator(args.url, payload)

    if args.dump_json:
        args.dump_json.write_text(json.dumps(data, indent=2))
        print(f"Wrote response to {args.dump_json}")

    for line in format_response_summary(data):
        print(line)

    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI usage
    raise SystemExit(main())
