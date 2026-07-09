#!/usr/bin/env python
from __future__ import annotations
import argparse, subprocess, shutil, re
from dwg_common import *

def ask_docs(query: str, timeout: int):
    if not shutil.which('uip'):
        return 'uip CLI not found; docs check skipped.'
    try:
        p=subprocess.run(['uip','docsai','ask',query],text=True,capture_output=True,timeout=timeout)
        return (p.stdout or p.stderr or '').strip()[:2000]
    except Exception as e:
        return f'docs query failed: {type(e).__name__}: {e}'

def main():
    ap=argparse.ArgumentParser(description='Check wiki claims against official docs via uip docsai ask.'); ap.add_argument('--wiki',required=True); ap.add_argument('--db'); ap.add_argument('--page'); ap.add_argument('--term'); ap.add_argument('--limit',type=int,default=5); ap.add_argument('--timeout',type=int,default=45); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); conn=connect(db_path(wiki,a.db),readonly=True)
    clauses=[]; params=[]
    if a.page: clauses.append('page_path LIKE ?'); params.append(f'%{a.page}%')
    if a.term: clauses.append('claim_text LIKE ?'); params.append(f'%{a.term}%')
    where='WHERE '+' AND '.join(clauses) if clauses else ''
    claims=conn.execute(f"SELECT page_path,heading,claim_text,claim_kind FROM claims {where} AND claim_kind IN ('decision_rule','procedure_or_config','symptom_or_boundary') ORDER BY evidence_count DESC LIMIT ?" if where else "SELECT page_path,heading,claim_text,claim_kind FROM claims WHERE claim_kind IN ('decision_rule','procedure_or_config','symptom_or_boundary') ORDER BY evidence_count DESC LIMIT ?", params+[a.limit]).fetchall()
    out=[]
    for c in claims:
        q=f"For UiPath, verify this claim and cite current docs if possible: {c['claim_text']}"
        ans='DRY RUN: '+q if a.dry_run else ask_docs(q,a.timeout)
        status='skipped' if a.dry_run else ('no-uip-or-failed' if ans.lower().startswith(('uip cli not found','docs query failed')) else 'checked')
        out.append({'page_path':c['page_path'],'claim_kind':c['claim_kind'],'query':q[:220],'status':status,'docs_answer':ans[:700]})
    if out and not a.dry_run:
        content='# Docs Grounding Check\n\n'+'\n'.join(f"## {r['page_path']}\n- Claim/query: {r['query']}\n- Status: {r['status']}\n- Docs answer: {r['docs_answer']}\n" for r in out)
        path=write_report(wiki,'docs-grounding-check',content); append_log(wiki,'audit','docs grounding',[f'Wrote {path.relative_to(wiki).as_posix()} for {len(out)} claims.'])
    emit(out,a.format); conn.close()
if __name__=='__main__': main()
