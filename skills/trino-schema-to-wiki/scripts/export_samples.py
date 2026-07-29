"""Сэмплы таблиц Trino-схемы: CSV + выровненная markdown-таблица (tabulate).

Запуск (из любого каталога):
  uv run --with trino --with tabulate python export_samples.py \
    --server <mcp-сервер> --catalog <каталог> --schema <схема> \
    --tables <таблица1,таблица2> --rows 15 --out-dir ./samples

Креды берёт из ~/.claude.json → mcpServers[<server>].env (TRINO_*), не печатает.
--snapshot-col <колонка> — метка потока загрузки: срез = последний снапшот по
литералу; без неё (дефолт) — просто LIMIT без фиксации снапшота.
--drop-cols a,b — исключить колонки (например, широкие хэш-ключи) из сэмпла.
"""

import argparse
import csv
import json
import os
from pathlib import Path

import trino
import urllib3
from tabulate import tabulate

urllib3.disable_warnings()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="имя MCP-сервера Trino в ~/.claude.json")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--tables", required=True, help="через запятую")
    ap.add_argument("--rows", type=int, default=15)
    ap.add_argument("--snapshot-col", default="", help="колонка-метка потока загрузки")
    ap.add_argument("--drop-cols", default="", help="колонки, исключаемые из сэмпла")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    drop = {c.strip() for c in args.drop_cols.split(",") if c.strip()}

    cfg = json.loads(Path(os.path.expanduser("~/.claude.json")).read_text())
    env = cfg["mcpServers"][args.server]["env"]
    os.environ.setdefault("NO_PROXY", env.get("NO_PROXY", "*"))
    os.environ.setdefault("no_proxy", env.get("no_proxy", "*"))
    conn = trino.dbapi.connect(
        host=env["TRINO_HOST"],
        port=int(env.get("TRINO_PORT", 443)),
        user=env["TRINO_USER"],
        http_scheme=env.get("TRINO_SCHEME", "https"),
        auth=trino.auth.BasicAuthentication(env["TRINO_USER"], env["TRINO_PASSWORD"]),
        verify=False,
    )
    cur = conn.cursor()

    report = []
    for t in [x.strip() for x in args.tables.split(",") if x.strip()]:
        fq = f"{args.catalog}.{args.schema}.{t}"
        snapshot = None
        if args.snapshot_col:
            cur.execute(f"SELECT cast(max({args.snapshot_col}) as varchar) FROM {fq}")
            snapshot = cur.fetchone()[0]
            where = f"WHERE {args.snapshot_col} = timestamp '{snapshot}'" if snapshot else ""
        else:
            where = ""
        cur.execute(f"SELECT * FROM {fq} {where} LIMIT {args.rows}")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        keep = [i for i, c in enumerate(cols) if c not in drop]
        cols_k = [cols[i] for i in keep]
        rows_k = [["" if r[i] is None else str(r[i]) for i in keep] for r in rows]

        with (out_dir / f"{t}.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols_k)
            w.writerows(rows_k)
        md = tabulate(rows_k, headers=cols_k, tablefmt="github", disable_numparse=True)
        (out_dir / f"{t}.md").write_text(md)

        width = max((len(line) for line in md.splitlines()), default=0)
        report.append({"table": t, "rows": len(rows_k), "cols": len(cols_k), "snapshot": snapshot, "md_width": width})
        print(f"ok {t}: rows={len(rows_k)} snapshot={snapshot} md_width={width}", flush=True)

    (out_dir / "_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
