#!/usr/bin/env bash
set -euo pipefail
cd /var/www/pulseboard

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git remote -v | grep -q .; then
    echo "[deploy] pulling…"
    git pull --ff-only
  else
    echo "[deploy] no git remote configured; skipping pull"
  fi
fi

echo "[deploy] running builder…"
/usr/local/bin/pulseboard_build

echo "[deploy] reloading nginx (if permitted)…"
if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  sudo systemctl reload nginx
else
  echo "[deploy] no passwordless sudo; reload nginx manually if needed"
fi

echo "[deploy] done"
