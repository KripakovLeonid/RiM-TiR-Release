#!/usr/bin/env bash
set -euo pipefail

MANIFEST_PATH="${MANIFEST_PATH:-manifests/client-linux-amd64.yaml}"
TARGET_ID="${TARGET_ID:-}"

if [ -z "$TARGET_ID" ]; then
  TARGET_ID="$(python3 - <<PY
import yaml
with open("$MANIFEST_PATH", encoding="utf-8") as handle:
    print(yaml.safe_load(handle)["target"]["id"])
PY
)"
fi

python3 -m py_compile packaging/build_suite.py

python3 packaging/build_suite.py \
  --manifest "$MANIFEST_PATH" \
  --dist-dir "dist/$TARGET_ID" \
  --work-dir "work/$TARGET_ID"
