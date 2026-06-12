#!/usr/bin/env bash
set -euo pipefail

MANIFEST_PATH="${MANIFEST_PATH:-manifests/suite-dev.yaml}"
TARGET_ID="${TARGET_ID:-}"
CREATE_DUMMY_ARTIFACTS="${CREATE_DUMMY_ARTIFACTS:-false}"

if [ -z "$TARGET_ID" ]; then
  TARGET_ID="$(python - <<PY
import yaml
with open("$MANIFEST_PATH", encoding="utf-8") as handle:
    print(yaml.safe_load(handle)["target"]["id"])
PY
)"
fi

python -m py_compile packaging/build_suite.py packaging/create_dummy_artifacts.py

if [ "$CREATE_DUMMY_ARTIFACTS" = "true" ]; then
  python packaging/create_dummy_artifacts.py
fi

python packaging/build_suite.py \
  --manifest "$MANIFEST_PATH" \
  --dist-dir "dist/$TARGET_ID" \
  --work-dir "work/$TARGET_ID"
