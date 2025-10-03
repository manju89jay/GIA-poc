#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <pr-number> [--dry-run]" >&2
  exit 1
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY environment variable is required." >&2
  exit 1
fi

PR_NUMBER="$1"
shift || true

IMAGE="ghcr.io/qodo-ai/pr-agent:latest"
CONFIG=".github/ai-review/config.yml"
OWNERS=".github/ai-review/owners.yml"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Pulling $IMAGE ..."
  docker pull "$IMAGE"
fi

docker run --rm \
  -e OPENAI_API_KEY \
  -e GITHUB_TOKEN \
  -e PR_NUMBER="$PR_NUMBER" \
  -v "$(pwd)":/repo \
  "$IMAGE" \
  --repo "$(basename "$(git rev-parse --show-toplevel)")" \
  --pr "$PR_NUMBER" \
  --config "/repo/${CONFIG}" \
  --owners-config "/repo/${OWNERS}" "$@"
