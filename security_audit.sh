#!/bin/bash
set -e

# Backend, ML, Workers (Python)
for service in backend ml-service workers; do
  echo "\n=== Security audit for $service ==="
  if [ -f "$service/requirements.txt" ]; then
    echo "- Bandit (static code analysis)"
    bandit -r $service || true
    echo "- Safety (dependency vulnerabilities)"
    safety check -r $service/requirements.txt || true
  fi
done

# Frontend (Node.js)
if [ -f frontend/package.json ]; then
  echo "\n=== Security audit for frontend ==="
  cd frontend
  npm audit --audit-level=moderate || true
  cd ..
fi

echo "\nSecurity audit complete." 