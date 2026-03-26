#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
EXAMPLE_FILE="${ROOT_DIR}/.env.example"

if [[ -f "${ENV_FILE}" ]]; then
  echo ".env already exists: ${ENV_FILE}"
  exit 0
fi

if [[ ! -f "${EXAMPLE_FILE}" ]]; then
  echo "Missing .env.example at ${EXAMPLE_FILE}"
  exit 1
fi

cp "${EXAMPLE_FILE}" "${ENV_FILE}"

generate_secret() {
  openssl rand -hex 32
}

set_kv() {
  local key="$1"
  local value="$2"
  if grep -qE "^${key}=" "${ENV_FILE}"; then
    sed -i.bak -E "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}" && rm -f "${ENV_FILE}.bak"
  else
    echo "${key}=${value}" >> "${ENV_FILE}"
  fi
}

set_kv "SECRET_KEY" "$(generate_secret)"
set_kv "TRADING_ENCRYPTION_KEY" "$(generate_secret)"
set_kv "POSTGRES_PASSWORD" "$(generate_secret)"
set_kv "REDIS_PASSWORD" "$(generate_secret)"
set_kv "GRAFANA_ADMIN_PASSWORD" "$(generate_secret)"

echo ".env created at ${ENV_FILE}"
echo "Next: review and adjust values (Stripe, Telegram, CORS, domain URLs)."
