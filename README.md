# RiM-TiR-Release

Репозиторий манифестов и финальной сборки установочных комплектов RiM-TiR.

Этот репозиторий не хранит исходный код компонентов продукта. Компонентные
репозитории сами собирают свои артефакты, а этот репозиторий забирает готовые
артефакты и упаковывает их в установочные пакеты и общий комплект поставки.

## Текущий MVP

Первая версия сборщика работает с локальными артефактами и собирает:

- `rim-tir-client_<version>_<arch>.deb`
- `rim-tir-suite_<version>_<target>.tar.gz`
- `rim-tir-client_<version>_<target>.zip` для Windows
- `rim-tir-suite_<version>_<target>.zip` для Windows

Сейчас dev-сборка настроена под такие платформы:

- `linux-amd64`: Debian-пакет для Linux x86_64.
- `linux-arm64`: Debian-пакет для Linux ARM64.
- `linux-armhf`: Debian-пакет для Linux ARM 32-bit hard-float.
- `windows-amd64`: переносимый Windows-пакет с `tir-backend.exe`.

Создать тестовые артефакты и собрать комплект локально:

```bash
python3 packaging/create_dummy_artifacts.py
python3 packaging/build_suite.py --manifest manifests/suite-dev.yaml
python3 packaging/build_suite.py --manifest manifests/suite-dev-linux-arm64.yaml
python3 packaging/build_suite.py --manifest manifests/suite-dev-linux-armhf.yaml
python3 packaging/build_suite.py --manifest manifests/suite-dev-windows-amd64.yaml
```

Результат сборки появляется в папке `dist/`.

## CI

На время миграции поддерживаются оба CI:

- GitHub: `.github/workflows/release.yml`
- GitLab: `.gitlab-ci.yml`

GitLab CI использует переменную `MANIFEST_PATH`, чтобы выбрать манифест сборки.
Обычная dev-сборка запускается матрицей по всем текущим dev-манифестам:

- `manifests/suite-dev.yaml`
- `manifests/suite-dev-linux-arm64.yaml`
- `manifests/suite-dev-linux-armhf.yaml`
- `manifests/suite-dev-windows-amd64.yaml`

Для этих dev-манифестов pipeline сначала создает тестовые артефакты, а затем
собирает платформенные пакеты и общие архивы поставки.

При ручном запуске GitLab pipeline можно переопределить `MANIFEST_PATH` через
форму запуска.

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
