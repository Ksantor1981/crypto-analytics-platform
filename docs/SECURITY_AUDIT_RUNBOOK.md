# Security audit: структура и runbook

**Цель:** единый процесс проверки секретов, зависимостей и конфигов перед релизом и в CI.  
**Связанные документы:** [SECURITY_PUBLIC_REPO.md](./SECURITY_PUBLIC_REPO.md) (публичный репо, ротация, история git).

---

## 1. Фазы аудита (коротко)

| Фаза | Что проверяем | Инструменты | Критерий «готово» |
|------|----------------|-------------|---------------------|
| **A0** | Секреты в рабочей копии | `detect-secrets`, опционально pre-commit | Baseline актуален, новые находки разобраны |
| **A1** | Секреты во **всей** истории git | **TruffleHog** (или `git log -p` + ручной разбор) | Отчёт сохранён, найденные ключи в ротации |
| **A2** | Зависимости Python | `pip-audit` | Критичные CVE либо исправлены, либо задокументированы |
| **A3** | Зависимости npm | `npm audit` | Аналогично |
| **A4** | Конфиги деплоя | grep/CI job `security` в `.github/workflows/ci.yml` | Нет запрещённых паттернов в compose/helm |
| **A5** | Ротация | Ручной чеклист | Все ключи из плана в `SECURITY_PUBLIC_REPO.md` сменены |

---

## 2. Файлы в репозитории

| Файл | Назначение |
|------|------------|
| `.pre-commit-config.yaml` | Хуки: приватные ключи, merge conflict, EOF, trailing space, **detect-secrets** |
| `.secrets.baseline` | Baseline для `detect-secrets` (известные срабатывания / false positives после `audit`) |
| `requirements-dev.txt` | `pre-commit`, `detect-secrets` для локальной установки |

---

## 3. Первичная настройка (один раз)

Из корня репозитория (`crypto-analytics-platform/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pre-commit install
```

Проверка всех хуков на всём репо (без коммита):

```powershell
pre-commit run --all-files
```

---

## 4. Detect-secrets (обязательный минимум)

### Обновить baseline после изменений в коде

Если хук ругается на **новые** строки, либо исправьте код (уберите секрет), либо после проверки что это **не** секрет, добавьте в baseline:

```powershell
# Полный скан (исключая тяжёлые каталоги)
python -m detect_secrets scan --all-files `
  --exclude-files "(^|/)node_modules(/|$)" `
  --exclude-files "(^|/)\.next(/|$)" `
  --exclude-files "(^|/)\.venv(/|$)" `
  --exclude-files "package-lock\.json" `
  `
  . > .secrets.baseline
```

Интерактивная разметка false positive:

```powershell
python -m detect_secrets audit .secrets.baseline
```

Закоммитьте обновлённый `.secrets.baseline` вместе с кодом.

### Текущий baseline и исключения хука

Файл `.secrets.baseline` собран по целевым путям (CI, backend, тесты, compose, helm без `values.ci.yaml`, примеры env и т.д.) **без** сканирования Alembic-миграций и фикстур `workers/*.json` — для них в `.pre-commit-config.yaml` заданы `exclude` (шум hex/Base64, не секреты). При необходимости расширьте baseline: `detect-secrets scan --baseline .secrets.baseline <пути>` и закоммитьте.

Первый коммит с pre-commit: добавьте в git **четыре** файла — `.pre-commit-config.yaml`, `.secrets.baseline`, `requirements-dev.txt`, `docs/SECURITY_AUDIT_RUNBOOK.md` (и правку `SECURITY_PUBLIC_REPO.md`, если ссылка нужна).

---

## 5. TruffleHog (история git — критично для публичного репо)

Локально (нужен установленный [TruffleHog](https://github.com/trufflesecurity/trufflehog)):

```powershell
# Текущий репозиторий
trufflehog git file://. --json > temp/trufflehog-report.json

# Только verified (меньше шума)
trufflehog git file://. --only-verified --json > temp/trufflehog-verified.json
```

Если `trufflehog` не в PATH — используйте Docker (см. официальную документацию TruffleHog) или установите через `choco` / `scoop` / `go install`.

**Действия по результатам:** любые реальные ключи — **ротация**, см. [SECURITY_PUBLIC_REPO.md](./SECURITY_PUBLIC_REPO.md).

---

## 6. Pre-commit и CI

- **Локально:** `pre-commit` гоняет хуки на staged файлах.
- **CI:** в `.github/workflows/ci.yml` уже есть job `security` (grep, `pip-audit`, `npm audit`, helm).  
  Опционально добавить шаг:

```yaml
- name: pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

(Имеет смысл после того, как `pre-commit run --all-files` стабильно зелёный локально.)

---

## 7. Чеклист перед «production ready»

- [ ] `pre-commit run --all-files` без ошибок
- [ ] TruffleHog по истории выполнен, отчёт сохранён
- [ ] `.env` в `.gitignore`, `*.env` не в индексе
- [ ] `pip-audit -r backend/requirements.txt` просмотрен
- [ ] `npm audit` во frontend просмотрен
- [ ] Ротация ключей по плану из `SECURITY_PUBLIC_REPO.md`

---

## 8. Частые проблемы

| Симптом | Действие |
|---------|----------|
| `detect-secrets` fails на новом файле | Убрать секрет из кода или обновить baseline через `scan` + `audit` |
| Слишком много срабатываний в lock-файлах | Уже исключены в `.pre-commit-config.yaml` для `package-lock.json` и `*.lock` |
| TruffleHog на Windows | Использовать Docker или WSL2 или официальный binary |

---

*Последнее обновление структуры: 2026-04-03.*
