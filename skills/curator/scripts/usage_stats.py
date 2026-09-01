#!/usr/bin/env python3
"""Статистика использования по session-логам Claude Code.

Сканирует ~/.claude/projects/**/*.jsonl.
Режим по умолчанию — скиллы: вызовы Skill-тула и slash-команды (<command-name>).
Режим --mcp — вызовы MCP-тулов, агрегированные по серверу (mcp__<server>__*).
Вывод TSV: name<TAB>count<TAB>first_used<TAB>last_used.
Использование: usage_stats.py [--mcp] [logs_dir]
"""
import re
import sys
from pathlib import Path

args = [a for a in sys.argv[1:] if a != "--mcp"]
MCP_MODE = "--mcp" in sys.argv[1:]
LOGS = Path(args[0]) if args else Path.home() / ".claude" / "projects"

RE_SKILL = re.compile(r'"name":"Skill","input":\{[^{}]*?"skill":"([^"]+)"')
RE_CMD = re.compile(r"<command-name>/?([\w:-]+)</command-name>")
RE_MCP = re.compile(r'"name":"mcp__([\w-]+?)__')
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
                if MCP_MODE:
                    if '"name":"mcp__' not in line:
                        continue
                    m_ts = RE_TS.search(line)
                    day = m_ts.group(1) if m_ts else ""
                    for m in RE_MCP.finditer(line):
                        note(m.group(1), day)
                else:
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
