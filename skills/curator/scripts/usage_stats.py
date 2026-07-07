#!/usr/bin/env python3
"""Статистика использования скиллов по session-логам Claude Code.

Сканирует ~/.claude/projects/**/*.jsonl: вызовы Skill-тула и slash-команды
(<command-name>). Выводит TSV: skill<TAB>count<TAB>first_used<TAB>last_used.
Использование: usage_stats.py [logs_dir]
"""
import re
import sys
from pathlib import Path

LOGS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".claude" / "projects"

RE_SKILL = re.compile(r'"name":"Skill","input":\{[^{}]*?"skill":"([^"]+)"')
RE_CMD = re.compile(r"<command-name>/?([\w:-]+)</command-name>")
RE_TS = re.compile(r'"timestamp":"(\d{4}-\d{2}-\d{2})')

stats = {}  # name -> [count, first, last]

def note(name: str, day: str) -> None:
    s = stats.setdefault(name, [0, day, day])
    s[0] += 1
    if day:
        if not s[1] or day < s[1]:
            s[1] = day
        if not s[2] or day > s[2]:
            s[2] = day

for f in LOGS.rglob("*.jsonl"):
    try:
        with open(f, errors="replace") as fh:
            for line in fh:
                if '"name":"Skill"' not in line and "<command-name>" not in line:
                    continue
                m_ts = RE_TS.search(line)
                day = m_ts.group(1) if m_ts else ""
                for m in RE_SKILL.finditer(line):
                    note(m.group(1), day)
                for m in RE_CMD.finditer(line):
                    note(m.group(1), day)
    except OSError:
        continue

for name, (count, first, last) in sorted(stats.items(), key=lambda kv: kv[1][2] or "", reverse=True):
    print(f"{name}\t{count}\t{first or '?'}\t{last or '?'}")
