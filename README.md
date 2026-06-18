# RiM-TiR-Release

Репозиторий финальной сборки поставочного комплекта RiM-TiR.

Этот репозиторий не собирает исходный код компонентов. Компонентные
репозитории сами публикуют готовые исполняемые файлы, а `RiM-TiR-Release`
собирает из них единый продуктовый архив.

## Текущая Схема

На вход поступают готовые executable-компоненты:

- `TiR_client`
- `TiR_USPD`
- `TiR_Proto`
- `TiR_Update`
- `TiR_MQTT`

`TiR_client` собирается в backend-репозитории. Остальные компоненты приходят из
своих репозиториев. В этом репозитории они только проверяются, раскладываются по
папке `bin/`, описываются в `manifest.json` и упаковываются в общий архив.

## Платформы

Сейчас заведены manifest-файлы:

- `manifests/product-linux-amd64.yaml`
- `manifests/product-linux-arm64.yaml`
- `manifests/product-windows-amd64.yaml`

Если фактический список платформ будет другим, добавляется или удаляется только
соответствующий manifest и строка в CI matrix.

## Контракт Артефактов

Перед сборкой в `artifacts/<target>/` должны лежать готовые executable-файлы.

Пример для `linux-amd64`:

```text
artifacts/linux-amd64/
  TiR_client
  TiR_USPD
  TiR_Proto
  TiR_Update
  TiR_MQTT
```

Пример для `windows-amd64`:

```text
artifacts/windows-amd64/
  TiR_client.exe
  TiR_USPD.exe
  TiR_Proto.exe
  TiR_Update.exe
  TiR_MQTT.exe
```

## Локальная Сборка

```bash
python3 packaging/build_suite.py --manifest manifests/product-linux-amd64.yaml
```

Результат появляется в `dist/`:

- `rim-tir-product_<version>_<target>.tar.gz` для Linux
- `rim-tir-product_<version>_<target>.zip` для Windows
- `manifest.json`
- `checksums.sha256`

Внутри архива:

```text
bin/
  TiR_client
  TiR_USPD
  TiR_Proto
  TiR_Update
  TiR_MQTT
manifest.json
checksums.sha256
README.txt
```

## CI

На время миграции поддерживаются оба CI:

- GitHub: `.github/workflows/release.yml`
- GitLab: `.gitlab-ci.yml`

Pipeline не создает входные executable-файлы самостоятельно. Build job ожидает,
что component artifacts уже доступны по путям, указанным в выбранном manifest.

## Контейнер Сборки

Среда сборки описана в `ci/Dockerfile`.

Собрать image локально:

```bash
docker build -f ci/Dockerfile -t rim-tir-release-ci:local .
```

Проверить репозиторий внутри контейнера:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e PRODUCT_MANIFESTS="manifests/product-linux-amd64.yaml manifests/product-linux-arm64.yaml manifests/product-windows-amd64.yaml" \
  -v "$PWD:/workspace" \
  rim-tir-release-ci:local \
  ./ci/validate.sh
```

Собрать один target внутри контейнера:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e MANIFEST_PATH="manifests/product-linux-amd64.yaml" \
  -e TARGET_ID="linux-amd64" \
  -v "$PWD:/workspace" \
  rim-tir-release-ci:local \
  ./ci/build-release.sh
```

## Стиль Коммитов

Сообщения коммитов пишем на русском языке с коротким типом в начале:

```text
сборка: добавлена упаковка продуктового комплекта
ci: обновлена матрица сборки
доки: описан контракт артефактов
исправление: поправлена генерация checksums
```
