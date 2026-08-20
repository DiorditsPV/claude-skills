#!/usr/bin/env bash
# ensure.sh — идемпотентно гарантирует «чистый» Chrome с CDP-портом для скрейпинга
# сайтов с анти-бот-защитой. Если порт уже жив — ничего не делает.
#
# Usage:
#   ensure.sh [--persist] [--port N] [URL]
#     --persist   стабильный профиль ~/.cache/chrome-cdp-profile (cookies сохраняются между запусками)
#                 без флага — эфемерный /tmp/chrome-cdp (чистится при каждом старте)
#     --port N    порт CDP (по умолчанию 9222)
#     URL         опционально открыть страницу сразу
#
# Печатает webSocketDebuggerUrl и статус. Код возврата 0 — порт жив и отдаёт JSON.
set -euo pipefail

PORT=9222
PERSIST=0
URL=""
# порядок выбора бинарника: $CHROME_BIN → отдельный бандл «Chrome CDP» (своя иконка
# в Dock, собирается scripts/make-cdp-app.sh) → обычный Google Chrome
CDP_APP="$HOME/Applications/Chrome CDP.app/Contents/MacOS/Google Chrome"
if [ -z "${CHROME_BIN:-}" ]; then
  if [ -x "$CDP_APP" ]; then
    CHROME_BIN="$CDP_APP"
  else
    CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  fi
fi

while [ $# -gt 0 ]; do
  case "$1" in
    --persist) PERSIST=1; shift ;;
    --port)    PORT="$2"; shift 2 ;;
    --port=*)  PORT="${1#*=}"; shift ;;
    -*)        echo "unknown flag: $1" >&2; exit 2 ;;
    *)         URL="$1"; shift ;;
  esac
done

if [ "$PERSIST" = "1" ]; then
  PROFILE="$HOME/.cache/chrome-cdp-profile"
else
  PROFILE="/tmp/chrome-cdp"
fi

ver_url="http://127.0.0.1:${PORT}/json/version"

# 1. Уже запущен?
if curl -s --max-time 2 "$ver_url" >/dev/null 2>&1; then
  echo "✓ CDP уже запущен на :${PORT}"
  curl -s "$ver_url"
  exit 0
fi

# 2. Поднять браузер
[ -x "$CHROME_BIN" ] || { echo "Chrome не найден: $CHROME_BIN (задайте CHROME_BIN)" >&2; exit 1; }
[ "$PERSIST" = "1" ] || rm -rf "$PROFILE"
mkdir -p "$PROFILE"

echo "→ запускаю Chrome (профиль: $PROFILE, порт: $PORT, persist: $PERSIST)"
nohup "$CHROME_BIN" \
  --user-data-dir="$PROFILE" \
  --remote-debugging-port="$PORT" \
  --no-first-run --no-default-browser-check \
  "${URL:-about:blank}" >/dev/null 2>&1 &   # без вкладки нет page-таргета, и cdp.mjs не к чему подключиться

# 3. Дождаться порта (до ~15 c)
for _ in $(seq 1 30); do
  if curl -s --max-time 2 "$ver_url" >/dev/null 2>&1; then
    echo "✓ CDP поднят на :${PORT}"
    curl -s "$ver_url"
    exit 0
  fi
  sleep 0.5
done

echo "✗ порт :${PORT} не поднялся за 15 c" >&2
exit 1
