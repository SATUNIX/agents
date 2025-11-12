#!/usr/bin/env bash
set -euo pipefail

STATE_DIR=${STATE_DIR:-state}
ARTIFACT_DIR="$STATE_DIR/release_artifacts"

mkdir -p "$ARTIFACT_DIR"

for file in "$@"; do
  if [ -f "$file" ]; then
    cp "$file" "$ARTIFACT_DIR/"
  fi
done

echo "Artifacts copied to $ARTIFACT_DIR"
