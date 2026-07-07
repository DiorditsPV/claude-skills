#!/usr/bin/env python3
"""Чистит YouTube auto-sub VTT в плоский транскрипт.

Убирает таймкоды, инлайн-теги (<c>, <00:00:00.000>) и дубли строк
roll-up-субтитров (каждая строка в авто-сабах повторяется в 2+ кью).

Usage: vtt_to_transcript.py input.vtt [output.txt]
       (без output — пишет в stdout)
"""
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")


def clean(vtt_text: str) -> str:
    lines: list[str] = []
    for raw in vtt_text.splitlines():
        line = raw.strip()
        if (
            not line
            or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
            or TIMESTAMP_RE.match(line)
        ):
            continue
        line = TAG_RE.sub("", line).strip()
        if not line or line == "&nbsp;":
            continue
        # roll-up-дедуп: строка уже встречалась в хвосте
        if line in lines[-3:]:
            continue
        lines.append(line)
    return " ".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    text = clean(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text + "\n", encoding="utf-8")
        print(f"{sys.argv[2]}: ~{len(text.split())} слов")
    else:
        print(text)


if __name__ == "__main__":
    main()
