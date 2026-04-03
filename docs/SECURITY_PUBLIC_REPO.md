# Публичный репозиторий и утечки

Репозиторий [crypto-analytics-platform на GitHub](https://github.com/Ksantor1981/crypto-analytics-platform) **публичный**. Любые секреты, пароли и учебные шаблоны паролей, строки в `helm/values.yaml`, JWT/Stripe ключи, когда-либо попавшие в коммиты, нужно считать **раскрытыми навсегда** для истории git (даже после удаления из последнего коммита объекты остаются в `.git` до переписывания истории).

История очищалась: `git filter-repo --replace-text` (замена известных шаблонов на `REDACTED`) и удаление каталога `docs/archive/` из всей истории. Это **не отменяет** необходимость ротации реальных ключей.

## Что сделать немедленно

1. **Ротация всего, что могло быть в репо:** `SECRET_KEY`, пароли PostgreSQL и Redis, `STRIPE_*`, `TELEGRAM_*`, `GRAFANA_*`, `TRADING_ENCRYPTION_KEY`, webhook-секреты, любые API-ключи.
2. **Production и staging** — сменить креды независимо от того, «использовали ли вы» старые значения.
3. **Не восстанавливать** старые `values.yaml` с реальными строками из истории.

## Очистка истории git (опционально, деструктивно)

Если нужно убрать файлы из **всей** истории (артефакты с именами-команд, старые секреты):

1. Установить [git-filter-repo](https://github.com/newren/git-filter-repo).
2. Сделать резервную копию репозитория.
3. Пример удаления путей (подставьте точные имена из `git log --all --full-history --name-only`):

   ```bash
   git filter-repo --invert-paths \
     --path " --date=iso TASKS2.md  cat"
   ```

4. **`git push --force`** на все remotes; предупредить всех, у кого есть клоны (нужен `git fetch` + reset или переклонирование).

Даже после `filter-repo` **ротация секретов обязательна**: клоны и зеркала могли уже скачать старые объекты.

## Текущие меры в репозитории

- В `helm/values.yaml` нет готовых паролей — пустые поля и `required()` в шаблонах.
- Redis в Helm с `--requirepass`.
- Удалён дублирующий chart `infrastructure/helm/` (в шаблонах были захардкоженные креды).
- В `docker-compose*.yml` и `helm/` CI блокирует повторное появление известных слабых шаблонов (см. job `security` в `.github/workflows/ci.yml`).

## Bind-mount в dev

`docker-compose.yml` с `./backend:/app` предназначен **только для разработки**. Для сервера используйте `docker-compose.production.yml` или `docker-compose.deploy.yml` без монтирования исходников.

## Процесс аудита и pre-commit

Структура фаз, команды TruffleHog / detect-secrets, baseline и CI: **[SECURITY_AUDIT_RUNBOOK.md](./SECURITY_AUDIT_RUNBOOK.md)**.
