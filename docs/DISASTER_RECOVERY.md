# Disaster Recovery Plan

## Scope

- Backend API
- PostgreSQL
- Redis
- ML models and prediction service
- Stripe billing/webhooks

## RTO / RPO Targets

- **RTO**: 60 minutes for core API restore.
- **RPO**: 15 minutes for transactional data (subscriptions/payments/signals).

## Incident: PostgreSQL corruption / data loss

1. Stop writers (`backend`, workers, celery beat).
2. Restore latest backup to fresh DB instance.
3. Run migration consistency check:
   - `python backend/scripts/check_partial_reset_upgrade.py --yes` (staging only)
   - `alembic current -v`
4. Run smoke checks: `/health`, auth, signals list, subscription endpoints.
5. Re-enable writers and monitor error rate for 30 minutes.

## Incident: ML model quality regression / poisoning

1. Pin previous stable model via `ML_MODEL_VERSION`.
2. Roll back `ml-service/models/model_manifest.json` to last known good version.
3. Disable retrain scheduler temporarily.
4. Re-run evaluation on holdout set and publish report in docs.

## Incident: Stripe webhook delivery failures

1. Check webhook endpoint health (`/api/v1/stripe/webhook`).
2. Replay missed events from Stripe dashboard.
3. Run reconciliation job (DB subscriptions vs Stripe subscriptions).
4. Manually correct entitlements for mismatched users.

## Incident: Redis outage

1. Restart Redis and verify auth/password.
2. Confirm backend rate-limiter and task queue reconnect.
3. Flush only non-critical ephemeral keys if required.

## Communication

- Declare incident channel and owner.
- Post updates every 15 minutes until mitigated.
- Publish postmortem with root cause and follow-up actions.
