#!/usr/bin/env python
"""Query a Digital Worker grounding wiki SQLite knowledge database.

Generic over business-record corpora: the default schema uses `cases` for
historical compatibility, but the CLI exposes `record`/`records` language and can
query any source business object indexed into the same tables.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_LIMIT = 50


def wiki_path(value: str | None) -> Path:
    raw = value or os.environ.get("WIKI_PATH") or str(Path.home() / "wiki")
    return Path(raw).expanduser().resolve()


def db_path(wiki: Path, db_arg: str | None) -> Path:
    return Path(db_arg).expanduser().resolve() if db_arg else wiki / "_meta" / "knowledge.db"


def connect(db: Path) -> sqlite3.Connection:
    if not db.exists():
        raise SystemExit(f"knowledge DB not found: {db}\nCreate or refresh it at <wiki>/_meta/knowledge.db first.")
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    return conn


def is_read_only_sql(sql: str) -> bool:
    stripped = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.S | re.M).strip()
    if not stripped:
        return False
    # Allow a single read-only statement. SQLite PRAGMA table_info/list is useful.
    statements = [s.strip() for s in stripped.split(";") if s.strip()]
    if len(statements) != 1:
        return False
    first = statements[0].split(None, 1)[0].lower()
    if first in {"select", "with"}:
        return True
    if first == "pragma" and re.match(r"(?is)^pragma\s+(table_info|table_list|index_list|foreign_key_list|database_list)\b", statements[0]):
        return True
    return False


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def emit(rows: Sequence[dict], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if fmt == "csv":
        if not rows:
            return
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return
    # compact table
    if not rows:
        print("(no rows)")
        return
    cols = list(rows[0].keys())
    widths = {c: min(max(len(c), *(len(str(r.get(c, ""))) for r in rows[:100])), 80) for c in cols}
    def cell(c, v):
        s = str(v if v is not None else "")
        s = s.replace("\n", " ")
        return (s[: widths[c] - 1] + "…") if len(s) > widths[c] else s
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" | ".join(cell(c, r.get(c)).ljust(widths[c]) for c in cols))


def cmd_schema(conn: sqlite3.Connection, args) -> list[dict]:
    tables = conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
    out = []
    for t in tables:
        cols = conn.execute(f"PRAGMA table_info({quote_ident(t['name'])})").fetchall()
        out.append({"object": t["name"], "type": t["type"], "columns": ", ".join(c["name"] + " " + c["type"] for c in cols)})
    return out


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def cmd_counts(conn: sqlite3.Connection, args) -> list[dict]:
    names = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return [{"table": n, "rows": conn.execute(f"SELECT COUNT(*) AS n FROM {quote_ident(n)}").fetchone()["n"]} for n in names]


def cmd_sql(conn: sqlite3.Connection, args) -> list[dict]:
    if not is_read_only_sql(args.query):
        raise SystemExit("Refusing non-read-only SQL. Use a single SELECT/WITH or safe PRAGMA statement.")
    return rows_to_dicts(conn.execute(args.query).fetchmany(args.limit))


def cmd_record(conn: sqlite3.Connection, args) -> list[dict]:
    sql = """
    SELECT c.*, 
           (SELECT COUNT(*) FROM data_points dp WHERE dp.case_id = c.case_id) AS data_point_count,
           (SELECT COUNT(*) FROM claim_cases cc WHERE cc.case_id = c.case_id) AS exemplar_claim_count
    FROM cases c WHERE c.case_id = ?
    """
    return rows_to_dicts(conn.execute(sql, (args.id,)).fetchall())


def cmd_records(conn: sqlite3.Connection, args) -> list[dict]:
    clauses = []
    params = []
    if args.topic:
        clauses.append("topic LIKE ?")
        params.append(f"%{args.topic}%")
    if args.system:
        clauses.append("systems LIKE ?")
        params.append(f"%{args.system}%")
    if args.status:
        clauses.append("status = ?")
        params.append(args.status)
    if args.term:
        clauses.append("(gist LIKE ? OR notes LIKE ? OR topic LIKE ? OR systems LIKE ? OR case_type LIKE ?)")
        params.extend([f"%{args.term}%"] * 5)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
    SELECT case_id, status, case_type, topic, process_stage, root_cause, resolution_pattern, systems, novel, gist, pages_updated
    FROM cases {where}
    ORDER BY case_id
    LIMIT ?
    """
    params.append(args.limit)
    return rows_to_dicts(conn.execute(sql, params).fetchall())


def cmd_page(conn: sqlite3.Connection, args) -> list[dict]:
    return rows_to_dicts(conn.execute("""
    SELECT p.*, 
           (SELECT COUNT(*) FROM claims c WHERE c.page_path = p.page_path) AS claim_count,
           (SELECT COUNT(*) FROM data_points dp WHERE dp.page_path = p.page_path) AS data_point_count
    FROM pages p WHERE p.page_path = ? OR p.page_path LIKE ?
    ORDER BY p.page_path
    LIMIT ?
    """, (args.path, f"%{args.path}%", args.limit)).fetchall())


def cmd_claims(conn: sqlite3.Connection, args) -> list[dict]:
    clauses = []
    params = []
    if args.page:
        clauses.append("page_path LIKE ?")
        params.append(f"%{args.page}%")
    if args.term:
        clauses.append("claim_text LIKE ?")
        params.append(f"%{args.term}%")
    if args.kind:
        clauses.append("claim_kind = ?")
        params.append(args.kind)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(args.limit)
    return rows_to_dicts(conn.execute(f"""
    SELECT claim_id, page_path, heading, claim_kind, evidence_count, exemplar_case_ids, claim_text
    FROM claims {where}
    ORDER BY evidence_count DESC, page_path
    LIMIT ?
    """, params).fetchall())


def cmd_data_points(conn: sqlite3.Connection, args) -> list[dict]:
    clauses = []
    params = []
    if args.record_id:
        clauses.append("case_id = ?")
        params.append(args.record_id)
    if args.page:
        clauses.append("page_path LIKE ?")
        params.append(f"%{args.page}%")
    if args.type:
        clauses.append("data_type = ?")
        params.append(args.type)
    if args.term:
        clauses.append("normalized_text LIKE ?")
        params.append(f"%{args.term}%")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(args.limit)
    return rows_to_dicts(conn.execute(f"""
    SELECT case_id, page_path, data_type, source_field, confidence, normalized_text
    FROM data_points {where}
    ORDER BY data_type, case_id
    LIMIT ?
    """, params).fetchall())


def cmd_search(conn: sqlite3.Connection, args) -> list[dict]:
    term = f"%{args.term}%"
    rows = []
    rows.extend(dict(r, result_type="record") for r in conn.execute("""
      SELECT case_id AS id, topic AS title, gist AS text FROM cases
      WHERE case_id LIKE ? OR topic LIKE ? OR systems LIKE ? OR gist LIKE ? OR notes LIKE ?
      LIMIT ?
    """, (term, term, term, term, term, args.limit)).fetchall())
    rows.extend(dict(r, result_type="claim") for r in conn.execute("""
      SELECT claim_id AS id, page_path AS title, claim_text AS text FROM claims
      WHERE claim_text LIKE ? OR heading LIKE ? OR page_path LIKE ?
      LIMIT ?
    """, (term, term, term, args.limit)).fetchall())
    rows.extend(dict(r, result_type="data_point") for r in conn.execute("""
      SELECT case_id AS id, page_path AS title, normalized_text AS text FROM data_points
      WHERE normalized_text LIKE ? OR data_type LIKE ? OR page_path LIKE ?
      LIMIT ?
    """, (term, term, term, args.limit)).fetchall())
    return rows[: args.limit]


def cmd_top(conn: sqlite3.Connection, args) -> list[dict]:
    if args.by == "data_type":
        return rows_to_dicts(conn.execute("SELECT data_type, COUNT(*) AS count, COUNT(DISTINCT case_id) AS record_count FROM data_points GROUP BY data_type ORDER BY count DESC LIMIT ?", (args.limit,)).fetchall())
    if args.by == "page_claims":
        return rows_to_dicts(conn.execute("SELECT page_path, title, claim_count, summed_evidence FROM v_page_claim_counts ORDER BY claim_count DESC LIMIT ?", (args.limit,)).fetchall())
    if args.by == "page_data_points":
        return rows_to_dicts(conn.execute("SELECT page_path, COUNT(*) AS data_points, COUNT(DISTINCT case_id) AS record_count FROM data_points GROUP BY page_path ORDER BY data_points DESC LIMIT ?", (args.limit,)).fetchall())
    if args.by == "topics":
        return rows_to_dicts(conn.execute("SELECT topic, COUNT(*) AS records FROM cases GROUP BY topic ORDER BY records DESC LIMIT ?", (args.limit,)).fetchall())
    raise SystemExit(f"unknown --by value: {args.by}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Query _meta/knowledge.db for a Digital Worker grounding wiki.")
    p.add_argument("--wiki", help="Wiki path. Defaults to WIKI_PATH or ~/wiki.")
    p.add_argument("--db", help="Explicit SQLite DB path. Defaults to <wiki>/_meta/knowledge.db.")
    p.add_argument("--format", choices=["table", "json", "csv"], default="table")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("schema", help="Show tables/views and columns.").set_defaults(func=cmd_schema)
    sub.add_parser("counts", help="Show row counts by table.").set_defaults(func=cmd_counts)

    s = sub.add_parser("sql", help="Run read-only SQL (single SELECT/WITH or safe PRAGMA).")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_sql)

    s = sub.add_parser("record", help="Show one business record/case by ID.")
    s.add_argument("id")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("records", help="List/filter business records/cases.")
    s.add_argument("--topic")
    s.add_argument("--system")
    s.add_argument("--status")
    s.add_argument("--term")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_records)

    s = sub.add_parser("page", help="Show page metadata by path or path fragment.")
    s.add_argument("path")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_page)

    s = sub.add_parser("claims", help="Filter cited wiki claims.")
    s.add_argument("--page")
    s.add_argument("--term")
    s.add_argument("--kind")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_claims)

    s = sub.add_parser("data-points", help="Filter reusable extracted data points.")
    s.add_argument("--record-id")
    s.add_argument("--page")
    s.add_argument("--type")
    s.add_argument("--term")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_data_points)

    s = sub.add_parser("search", help="Search records, claims, and data points.")
    s.add_argument("term")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("top", help="Common summary queries.")
    s.add_argument("--by", choices=["data_type", "page_claims", "page_data_points", "topics"], default="data_type")
    s.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    s.set_defaults(func=cmd_top)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    wiki = wiki_path(args.wiki)
    db = db_path(wiki, args.db)
    conn = connect(db)
    try:
        rows = args.func(conn, args)
        emit(rows, args.format)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
