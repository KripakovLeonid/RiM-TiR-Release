# RiM-TiR-Release

Репозиторий манифестов и финальной сборки установочных комплектов RiM-TiR.

Этот репозиторий не хранит исходный код компонентов продукта. Компонентные
репозитории сами собирают свои артефакты, а этот репозиторий забирает готовые
артефакты и упаковывает их в установочные пакеты и общий комплект поставки.

## Текущая Сборка

Репозиторий сейчас собирает только клиентскую часть RiM-TiR. На вход нужны
готовые артефакты frontend и backend, указанные в выбранном manifest.

На выходе собираются:

- `rim-tir-client_<version>_<arch>.deb`
- `rim-tir-suite_<version>_<target>.tar.gz`
- `rim-tir-client_<version>_<target>.zip` для Windows
- `rim-tir-suite_<version>_<target>.zip` для Windows

Сейчас сборка клиентской части настроена под такие платформы:

- `linux-amd64`: Debian-пакет для Linux x86_64.
- `linux-arm64`: Debian-пакет для Linux ARM64.
- `linux-armhf`: Debian-пакет для Linux ARM 32-bit hard-float.
- `windows-amd64`: переносимый Windows-пакет с `tir-backend.exe`.

Перед сборкой положите реальные артефакты в пути, указанные в manifest:

```text
artifacts/frontend-dist.zip
artifacts/backend-linux-amd64.tar.gz
artifacts/backend-linux-arm64.tar.gz
artifacts/backend-linux-armhf.tar.gz
artifacts/backend-windows-amd64.zip
```

Собрать комплект локально:

```bash
python3 packaging/build_suite.py --manifest manifests/client-linux-amd64.yaml
python3 packaging/build_suite.py --manifest manifests/client-linux-arm64.yaml
python3 packaging/build_suite.py --manifest manifests/client-linux-armhf.yaml
python3 packaging/build_suite.py --manifest manifests/client-windows-amd64.yaml
```

Результат сборки появляется в папке `dist/`.

## CI

На время миграции поддерживаются оба CI:

- GitHub: `.github/workflows/release.yml`
- GitLab: `.gitlab-ci.yml`

GitLab CI использует переменную `MANIFEST_PATH`, чтобы выбрать манифест сборки.
Ручная сборка запускается матрицей по всем текущим клиентским манифестам:

- `manifests/client-linux-amd64.yaml`
- `manifests/client-linux-arm64.yaml`
- `manifests/client-linux-armhf.yaml`
- `manifests/client-windows-amd64.yaml`

Pipeline не создает входные артефакты самостоятельно. Build job запускается вручную и
ожидает, что настоящие артефакты уже доступны по путям, указанным в manifest.

При ручном запуске GitLab pipeline можно переопределить `MANIFEST_PATH` через
форму запуска.

## Контейнер Сборки

Среда сборки описана в `ci/Dockerfile`. Внутри контейнера есть Python,
зависимости из `packaging/requirements.txt` и системные утилиты для сборки
Debian-пакетов и архивов.

Собрать image локально:

```bash
docker build -f ci/Dockerfile -t rim-tir-release-ci:local .
```

Проверить репозиторий внутри контейнера:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e CLIENT_MANIFESTS="manifests/client-linux-amd64.yaml manifests/client-linux-arm64.yaml manifests/client-linux-armhf.yaml manifests/client-windows-amd64.yaml" \
  -v "$PWD:/workspace" \
  rim-tir-release-ci:local \
  ./ci/validate.sh
```

Собрать один target внутри контейнера:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MANIFEST_PATH="manifests/client-linux-arm64.yaml" \
  -e TARGET_ID="linux-arm64" \
  -v "$PWD:/workspace" \
  rim-tir-release-ci:local \
  ./ci/build-release.sh
```

В GitHub Actions image собирается командой `docker build`, после чего сборка
каждой платформы запускается через `docker run`.

В GitLab можно оставить текущий `python:3.12-slim` или заменить переменную
`RELEASE_CI_IMAGE` на заранее опубликованный образ из локального GitLab
Container Registry, собранный из `ci/Dockerfile`.

## Стиль Коммитов

Сообщения коммитов пишем на русском языке с коротким типом в начале:

```text
сборка: добавить сборку клиентского пакета
ci: добавить проверку манифеста
доки: описать формат артефактов
исправление: поправить генерацию checksums
```

## Структура

```text
manifests/            Манифесты комплектов поставки.
ci/                   Контейнер сборки и команды для CI.
packaging/            Скрипты сборки.
templates/client/     Шаблон Debian-пакета клиентской части.
templates/suite/      Скрипты и README для общего архива поставки.
```

## Контракт Артефактов

Артефакт frontend:

```text
dist/
  index.html
  assets/
```

Артефакт backend:

```text
bin/tir-backend
```

Для Windows backend-артефакт должен содержать:

```text
bin/tir-backend.exe
```

В будущих манифестах источниками смогут быть не локальные файлы, а release
assets из GitHub или GitLab.
