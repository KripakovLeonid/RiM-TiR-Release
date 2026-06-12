#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from string import Template
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


def copy_tree_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def extract_archive(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    suffixes = "".join(archive_path.suffixes)
    if suffixes.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(destination)
        return
    if suffixes.endswith(".tar.gz") or suffixes.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(destination, filter="data")
        return
    raise ValueError(f"unsupported archive type: {archive_path}")


def artifact_path(manifest_path: Path, component: dict[str, Any]) -> Path:
    source = component.get("source") or {}
    if source.get("type") != "local":
        raise ValueError("MVP supports only local component sources")
    raw_path = source.get("path")
    if not raw_path:
        raise ValueError("local source path is required")
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_path.parent.parent / path
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def render_template_file(src: Path, dst: Path, values: dict[str, str]) -> None:
    text = Template(src.read_text(encoding="utf-8")).safe_substitute(values)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def copy_template_tree(template_dir: Path, package_root: Path, values: dict[str, str]) -> None:
    for src in template_dir.rglob("*"):
        if src.is_dir():
            continue
        relative = src.relative_to(template_dir)
        dst = package_root / relative
        render_template_file(src, dst, values)
        if any(part == "DEBIAN" for part in relative.parts) and src.name in {
            "postinst",
            "prerm",
            "postrm",
        }:
            dst.chmod(0o755)


def find_single_file(root: Path, names: list[str]) -> Path:
    for name in names:
        matches = list(root.rglob(name))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"none of {names} found under {root}")


def find_dir(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_dir()]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"directory {name} not found under {root}")


def build_deb(package_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalize_deb_permissions(package_root)
    subprocess.run(
        ["dpkg-deb", "--build", "--root-owner-group", str(package_root), str(output_path)],
        check=True,
    )


def build_zip(source_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_root.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, path.relative_to(source_root))


def normalize_deb_permissions(package_root: Path) -> None:
    package_root.chmod(0o755)
    for path in package_root.rglob("*"):
        if path.is_dir():
            path.chmod(0o755)
            continue
        executable = os.access(path, os.X_OK)
        path.chmod(0o755 if executable else 0o644)


def make_client_package(
    manifest: dict[str, Any],
    manifest_path: Path,
    extract_root: Path,
    dist_dir: Path,
) -> Path:
    target = manifest["target"]
    if target["os"] == "windows":
        return make_windows_client_package(manifest, manifest_path, extract_root, dist_dir)
    return make_linux_client_package(manifest, manifest_path, extract_root, dist_dir)


def make_linux_client_package(
    manifest: dict[str, Any],
    manifest_path: Path,
    extract_root: Path,
    dist_dir: Path,
) -> Path:
    suite = manifest["suite"]
    target = manifest["target"]
    package_info = manifest["packages"]["client"]
    package_name = package_info["name"]
    version = suite["version"]
    deb_arch = target["deb_arch"]

    package_root = extract_root / "packages" / package_name
    template_dir = ROOT / "templates" / "client"
    values = {
        "package_name": package_name,
        "version": version,
        "architecture": deb_arch,
        "maintainer": package_info["maintainer"],
        "description": package_info["description"],
    }
    copy_template_tree(template_dir, package_root, values)

    frontend_archive = artifact_path(manifest_path, manifest["components"]["frontend"])
    backend_archive = artifact_path(manifest_path, manifest["components"]["backend"])
    frontend_extract = extract_root / "components" / "frontend"
    backend_extract = extract_root / "components" / "backend"
    extract_archive(frontend_archive, frontend_extract)
    extract_archive(backend_archive, backend_extract)

    web_src = find_dir(frontend_extract, "dist")
    web_dst = package_root / "usr" / "share" / "rim-tir-client" / "web"
    copy_tree_contents(web_src, web_dst)

    backend_binary = find_single_file(backend_extract, ["tir-backend", "tir-backend.exe"])
    backend_dst = package_root / "usr" / "bin" / "rim-tir-backend"
    backend_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backend_binary, backend_dst)
    backend_dst.chmod(0o755)

    output = dist_dir / f"{package_name}_{version}_{deb_arch}.deb"
    build_deb(package_root, output)
    return output


def make_windows_client_package(
    manifest: dict[str, Any],
    manifest_path: Path,
    extract_root: Path,
    dist_dir: Path,
) -> Path:
    suite = manifest["suite"]
    target = manifest["target"]
    package_info = manifest["packages"]["client"]
    package_name = package_info["name"]
    version = suite["version"]
    target_id = target["id"]

    package_root = extract_root / "packages" / f"{package_name}_{version}_{target_id}"
    template_dir = ROOT / "templates" / "windows-client"
    values = {
        "package_name": package_name,
        "version": version,
        "target_id": target_id,
        "maintainer": package_info["maintainer"],
        "description": package_info["description"],
    }
    copy_template_tree(template_dir, package_root, values)

    frontend_archive = artifact_path(manifest_path, manifest["components"]["frontend"])
    backend_archive = artifact_path(manifest_path, manifest["components"]["backend"])
    frontend_extract = extract_root / "components" / "frontend"
    backend_extract = extract_root / "components" / "backend"
    extract_archive(frontend_archive, frontend_extract)
    extract_archive(backend_archive, backend_extract)

    web_src = find_dir(frontend_extract, "dist")
    web_dst = package_root / "web"
    copy_tree_contents(web_src, web_dst)

    backend_binary = find_single_file(backend_extract, ["tir-backend.exe"])
    backend_dst = package_root / "bin" / "tir-backend.exe"
    backend_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backend_binary, backend_dst)

    output = dist_dir / f"{package_name}_{version}_{target_id}.zip"
    build_zip(package_root, output)
    return output


PACKAGE_BUILDERS = {
    "client": make_client_package,
}


PACKAGE_SERVICES = {
    "client": "rim-tir-client.service",
}


def enabled_packages(manifest: dict[str, Any]) -> list[str]:
    packages = manifest.get("packages") or {}
    enabled = packages.get("enabled")
    if enabled is None:
        return ["client"]
    if not isinstance(enabled, list) or not all(isinstance(item, str) for item in enabled):
        raise ValueError("packages.enabled must be a list of package ids")
    unknown = [item for item in enabled if item not in PACKAGE_BUILDERS]
    if unknown:
        raise ValueError(f"unsupported package ids: {', '.join(unknown)}")
    return enabled


def make_release_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    components = {}
    for name, component in manifest["components"].items():
        path = artifact_path(manifest_path, component)
        components[name] = {
            "product": component.get("product"),
            "repo": component.get("repo"),
            "source": component.get("source"),
            "artifact_sha256": sha256_file(path),
        }
    return {
        "suite": manifest["suite"],
        "target": manifest["target"],
        "components": components,
    }


def write_checksums(files: list[Path], output: Path) -> None:
    lines = [f"{sha256_file(path)}  {path.name}\n" for path in files]
    output.write_text("".join(lines), encoding="utf-8")


def make_suite_bundle(
    manifest: dict[str, Any],
    release_manifest: dict[str, Any],
    package_files: list[Path],
    work_dir: Path,
    dist_dir: Path,
) -> Path:
    version = manifest["suite"]["version"]
    target_id = manifest["target"]["id"]
    suite_name = f"rim-tir-suite_{version}_{target_id}"
    suite_root = work_dir / suite_name
    packages_dir = suite_root / "packages"
    packages_dir.mkdir(parents=True)

    for package_file in package_files:
        shutil.copy2(package_file, packages_dir / package_file.name)

    manifest_json = suite_root / "manifest.json"
    manifest_json.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    checksums = suite_root / "checksums.sha256"
    write_checksums([packages_dir / path.name for path in package_files] + [manifest_json], checksums)

    suite_template = ROOT / "templates" / (
        "windows-suite" if manifest["target"]["os"] == "windows" else "suite"
    )
    copy_template_tree(
        suite_template,
        suite_root,
        {
            "suite_name": suite_name,
            "version": version,
            "target_id": target_id,
            "client_package_file": next(
                (path.name for path in package_files if path.name.startswith("rim-tir-client_")),
                "",
            ),
            "package_names": " ".join(path.name.split("_", 1)[0] for path in package_files),
            "service_names": " ".join(
                service for package_id in enabled_packages(manifest)
                if (service := PACKAGE_SERVICES.get(package_id))
            ),
        },
    )
    for script_name in ["install.sh", "uninstall.sh", "install-client.bat"]:
        path = suite_root / script_name
        if path.exists():
            path.chmod(0o755)

    if manifest["target"]["os"] == "windows":
        output = dist_dir / f"{suite_name}.zip"
        build_zip(suite_root, output)
    else:
        output = dist_dir / f"{suite_name}.tar.gz"
        with tarfile.open(output, "w:gz") as archive:
            archive.add(suite_root, arcname=suite_name)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="manifests/suite-dev.yaml")
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

    package_files = [
        PACKAGE_BUILDERS[package_id](manifest, manifest_path, work_dir, dist_dir)
        for package_id in enabled_packages(manifest)
    ]
    release_manifest = make_release_manifest(manifest, manifest_path)
    release_manifest_path = dist_dir / "manifest.json"
    release_manifest_path.write_text(
        json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    suite_bundle = make_suite_bundle(manifest, release_manifest, package_files, work_dir, dist_dir)
    write_checksums(package_files + [release_manifest_path, suite_bundle], dist_dir / "checksums.sha256")

    print("Built release artifacts:")
    for path in package_files + [release_manifest_path, suite_bundle, dist_dir / "checksums.sha256"]:
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
