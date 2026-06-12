# RiM-TiR-Release

Repository for RiM-TiR release manifests and final distributable builds.

The repository does not own component source code. Component repositories build
their own artifacts, and this repository assembles those artifacts into
installable packages and a suite bundle.

## Current MVP

The first implementation supports local artifacts and builds:

- `rim-tir-client_<version>_<arch>.deb`
- `rim-tir-protocol_<version>_<arch>.deb`
- `rim-tir-suite_<version>_<target>.tar.gz`

Create sample artifacts and build the suite locally:

```bash
python3 packaging/create_dummy_artifacts.py
python3 packaging/build_suite.py --manifest manifests/suite-dev.yaml
```

Output is written to `dist/`.

## CI

GitHub Actions and GitLab CI are both present during the migration period:

- GitHub: `.github/workflows/release.yml`
- GitLab: `.gitlab-ci.yml`

GitLab CI uses `MANIFEST_PATH` to choose the suite manifest. The default value
is `manifests/suite-dev.yaml`, which creates dummy component artifacts before
building the Debian packages and suite archive.

Manual GitLab runs can override `MANIFEST_PATH` from the pipeline form.

## Layout

```text
manifests/            Suite manifests.
packaging/            Build scripts.
templates/client/     Debian package template for client package.
templates/protocol/   Debian package template for protocol package.
templates/suite/      Final bundle scripts and README.
```

## Component Contract

Frontend artifact:

```text
dist/
  index.html
  assets/
```

Backend artifact:

```text
bin/tir-backend
```

Protocol artifact:

```text
bin/tir-protocol
lib/                  optional runtime libraries
```

Future manifests can point to GitHub Release assets instead of local files.
