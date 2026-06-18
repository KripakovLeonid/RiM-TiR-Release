#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "dist"
DEFAULT_WORK = ROOT / "work"


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a mapping")
    return manifest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def artifact_path(manifest_path: Path, component: dict[str, Any]) -> Path:
    source = component.get("source") or {}
    if source.get("type") != "local":
        raise ValueError("only local component sources are supported now")

    raw_path = source.get("path")
    if not raw_path:
        raise ValueError("local source path is required")

    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_path.parent.parent / path
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError(f"component artifact must be a file: {path}")
    return path


def build_zip(source_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_root.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, path.relative_to(source_root))


def write_checksums(files: list[Path], output: Path) -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(output.parent)}\n" for path in files]
    output.write_text("".join(lines), encoding="utf-8")


def normalize_executable(path: Path, target_os: str) -> None:
    if target_os != "windows":
        path.chmod(0o755)


def build_release_manifest(
    manifest: dict[str, Any],
    manifest_path: Path,
    packaged_files: dict[str, Path],
) -> dict[str, Any]:
    components = {}
    for component_id, component in manifest["components"].items():
        source_path = artifact_path(manifest_path, component)
        packaged_path = packaged_files[component_id]
        components[component_id] = {
            "product": component["product"],
            "repo": component.get("repo", ""),
            "source": component["source"],
            "executable": component["executable"],
            "artifact_sha256": sha256_file(source_path),
            "packaged_path": str(packaged_path),
        }

    return {
        "suite": manifest["suite"],
        "target": manifest["target"],
        "components": components,
    }


def write_readme(manifest: dict[str, Any], suite_root: Path) -> None:
    suite = manifest["suite"]
    target = manifest["target"]
    component_lines = "\n".join(
        f"- {component['product']}: bin/{component['executable']}"
        for component in manifest["components"].values()
    )
    text = (
        f"{suite['name']} {suite['version']} ({target['id']})\n\n"
        "Комплект содержит готовые исполняемые файлы компонентов RiM-TiR.\n\n"
        "Компоненты:\n"
        f"{component_lines}\n\n"
        "Проверка целостности:\n"
        "  sha256sum -c checksums.sha256\n\n"
        "Конкретный порядок запуска и конфигурация компонентов задаются документацией продукта.\n"
    )
    (suite_root / "README.txt").write_text(text, encoding="utf-8")


def make_suite_bundle(manifest: dict[str, Any], manifest_path: Path, work_dir: Path, dist_dir: Path) -> Path:
    suite = manifest["suite"]
    target = manifest["target"]
    version = suite["version"]
    target_id = target["id"]
    suite_name = f"{suite['name']}_{version}_{target_id}"
    suite_root = work_dir / suite_name
    bin_dir = suite_root / "bin"
    bin_dir.mkdir(parents=True)

    packaged_files: dict[str, Path] = {}
    for component_id, component in manifest["components"].items():
        source_path = artifact_path(manifest_path, component)
        executable_name = component["executable"]
        destination = bin_dir / executable_name
        shutil.copy2(source_path, destination)
        normalize_executable(destination, target["os"])
        packaged_files[component_id] = destination.relative_to(suite_root)

    release_manifest = build_release_manifest(manifest, manifest_path, packaged_files)
    manifest_json = suite_root / "manifest.json"
    manifest_json.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_readme(manifest, suite_root)
    checksums = suite_root / "checksums.sha256"
    checksum_files = [suite_root / path for path in packaged_files.values()] + [
        manifest_json,
        suite_root / "README.txt",
    ]
    write_checksums(checksum_files, checksums)

    dist_dir.mkdir(parents=True, exist_ok=True)
    if target["os"] == "windows":
        output = dist_dir / f"{suite_name}.zip"
        build_zip(suite_root, output)
    else:
        output = dist_dir / f"{suite_name}.tar.gz"
        with tarfile.open(output, "w:gz") as archive:
            archive.add(suite_root, arcname=suite_name)

    release_manifest_path = dist_dir / "manifest.json"
    release_manifest_path.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_checksums([output, release_manifest_path], dist_dir / "checksums.sha256")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="manifests/product-linux-amd64.yaml")
    parser.add_argument("--dist-dir", default=str(DEFAULT_DIST))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    dist_dir = Path(args.dist_dir)
    if not dist_dir.is_absolute():
        dist_dir = ROOT / dist_dir
    work_dir = Path(args.work_dir)
    if not work_dir.is_absolute():
        work_dir = ROOT / work_dir

    manifest = load_manifest(manifest_path)
    ensure_clean_dir(dist_dir)
    ensure_clean_dir(work_dir)

    suite_bundle = make_suite_bundle(manifest, manifest_path, work_dir, dist_dir)

    print("Built release artifacts:")
    for path in [suite_bundle, dist_dir / "manifest.json", dist_dir / "checksums.sha256"]:
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
