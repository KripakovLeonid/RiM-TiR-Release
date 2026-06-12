#!/usr/bin/env bash
set -euo pipefail

python -m py_compile packaging/build_suite.py packaging/create_dummy_artifacts.py

python - <<'PY'
import os
from pathlib import Path
import yaml

paths = [
    Path(".gitlab-ci.yml"),
    Path(".github/workflows/release.yml"),
]
paths.extend(Path(path) for path in os.environ["DEV_MANIFESTS"].split())

for path in paths:
    with path.open(encoding="utf-8") as handle:
        yaml.safe_load(handle)
    print(f"OK {path}")
PY
