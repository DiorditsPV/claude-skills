#!/usr/bin/env bash
# make-cdp-app.sh — собирает отдельный бандл «Chrome CDP» (клон Google Chrome с красной
# иконкой и своим именем), чтобы служебный браузер скилла отличался в Dock и Cmd-Tab
# от личного Chrome.
#
# Идемпотентно: пересобирает бандл с нуля при каждом запуске.
# ПЕРЕЗАПУСКАТЬ после обновления Google Chrome — клон не обновляется сам.
#
# Usage:
#   make-cdp-app.sh [--src "/Applications/Google Chrome.app"] [--dst "$HOME/Applications/Chrome CDP.app"]
set -euo pipefail

SRC="/Applications/Google Chrome.app"
DST="$HOME/Applications/Chrome CDP.app"
NAME="Chrome CDP"

while [ $# -gt 0 ]; do
  case "$1" in
    --src) SRC="$2"; shift 2 ;;
    --dst) DST="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

[ -d "$SRC" ] || { echo "не найден исходный Chrome: $SRC" >&2; exit 1; }
python3 -c "import PIL" 2>/dev/null || { echo "нужен Pillow: pip3 install Pillow" >&2; exit 1; }

echo "→ клонирую $SRC → $DST"
mkdir -p "$(dirname "$DST")"
rm -rf "$DST"
# -c: APFS clone (copy-on-write, диск не расходуется); фолбэк — обычная копия
cp -Rc "$SRC" "$DST" 2>/dev/null || cp -R "$SRC" "$DST"

RES="$DST/Contents/Resources"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "→ бейджу иконку"
iconutil -c iconset "$RES/app.icns" -o "$WORK/app.iconset"
python3 - "$WORK/app.iconset" <<'PY'
import sys, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

iconset = pathlib.Path(sys.argv[1])
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

for png in sorted(iconset.glob("*.png")):
    im = Image.open(png).convert("RGBA")
    w, h = im.size
    # логотип обесцвечиваем и притемняем — красный бейдж должен быть единственным цветом
    r, g, b, a = im.split()
    base = Image.merge("RGBA", (*ImageEnhance.Brightness(
        Image.merge("RGB", (r, g, b)).convert("L").convert("RGB")).enhance(0.85).split(), a))

    # рисуем в 4x и уменьшаем — сглаженные края даже на 16 px
    S = 4
    layer = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([w*S*0.42, h*S*0.42, w*S*0.99, h*S*0.99], fill=(214, 34, 34, 255),
              outline=(255, 255, 255, 235), width=max(2, int(w*S*0.022)))
    if w >= 64:
        size = int(w * S * 0.20)
        try:
            font = ImageFont.truetype(FONT, size)
        except OSError:
            font = ImageFont.load_default()
        d.text((w*S*0.705, h*S*0.705), "CDP", font=font, fill=(255, 255, 255, 255),
               anchor="mm")
    badge = layer.resize((w, h), Image.LANCZOS)
    Image.alpha_composite(base, badge).save(png)
PY
iconutil -c icns "$WORK/app.iconset" -o "$RES/app.icns"

echo "→ переименовываю бандл в «${NAME}»"
PL="$DST/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleName $NAME" "$PL"
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $NAME" "$PL" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $NAME" "$PL"

# правка бандла ломает печать подписи — снимаем карантин и подписываем ad-hoc
xattr -cr "$DST" 2>/dev/null || true
if codesign --force --sign - "$DST"; then
  echo "→ подписан ad-hoc"
else
  echo "⚠ codesign не прошёл — если бандл не стартует, это первая причина" >&2
fi

echo "→ обновляю кеш иконок Dock"
touch "$DST"
killall Dock 2>/dev/null || true

echo "✓ готово: $DST"
echo "  запуск через скилл: bash \"\$SKILL_DIR/scripts/ensure.sh\" --persist"
