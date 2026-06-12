#!/usr/bin/env python3
from __future__ import annotations

import io
import shutil
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def write_executable_tar(path: Path, member_name: str, script: str) -> None:
    data = script.encode()
    info = tarfile.TarInfo(member_name)
    info.size = len(data)
    info.mode = 0o755

    with tarfile.open(path, "w:gz") as archive:
        archive.addfile(info, io.BytesIO(data))


def main() -> None:
    if ARTIFACTS.exists():
        shutil.rmtree(ARTIFACTS)
    ARTIFACTS.mkdir(parents=True)

    with zipfile.ZipFile(ARTIFACTS / "frontend-dist.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "dist/index.html",
            "<!doctype html><title>RiM-TiR dummy frontend</title><h1>RiM-TiR</h1>",
        )
        archive.writestr("dist/assets/app.js", "console.log('rim-tir dummy frontend');\n")

    write_executable_tar(
        ARTIFACTS / "backend-linux-amd64.tar.gz",
        "bin/tir-backend",
        "#!/bin/sh\n"
        "echo 'dummy tir-backend: use real go-tir-backend artifact for production'\n"
        "sleep 3600\n",
    )

    write_executable_tar(
        ARTIFACTS / "protocol-linux-amd64.tar.gz",
        "bin/tir-protocol",
        "#!/bin/sh\n"
        "echo 'dummy tir-protocol: use real protocol artifact for production'\n"
        "sleep 3600\n",
    )

    print(f"Created dummy artifacts in {ARTIFACTS}")


if __name__ == "__main__":
    main()
