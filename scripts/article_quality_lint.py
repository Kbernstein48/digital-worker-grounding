#!/usr/bin/env python
from __future__ import annotations
import argparse, re
from dwg_common import *
BAD=re.compile(r'(Additional To:|Original Message|\bFrom:|\bSent:|\bBCC:|\bCC:|\bSubject:|not the intended recipient|Caution: This email|thread::|<email>|<phone>|\.\.\.|Body:|Attachment:)',re.I)
CASEY=re.compile(r'\b(case|record)\s+\d{5,}|\bcase\s+(says|stated|was about|summary)',re.I)
REQ=['# ','scope','diagnosis','workflow','boundaries','related']
def main():
    ap=argparse.ArgumentParser(description='Enforce real wiki article, not case summary/snippet dump.'); ap.add_argument('--wiki',required=True); ap.add_argument('--format',choices=['table','json','csv'],default='table'); ap.add_argument('--write-report',action='store_true')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); rows=[]
    for p in durable_pages(wiki):
        rel=p.relative_to(wiki).as_posix(); txt=p.read_text(encoding='utf-8',errors='ignore'); low=txt.lower(); lines=txt.splitlines()
        if BAD.search(txt): rows.append({'severity':'error','page':rel,'finding':'raw source/truncation artifact'})
        if CASEY.search(txt): rows.append({'severity':'warn','page':rel,'finding':'case-summary-like prose'})
        ev=max([int(x) for x in re.findall(r'evidence:\s*(\d+)',txt)] or [0])
        if ev>=20 and len(lines)<40: rows.append({'severity':'warn','page':rel,'finding':'thin page under heavy evidence'})
        if rel.startswith('concepts/'):
            for need in REQ:
                if need not in low: rows.append({'severity':'info','page':rel,'finding':f'missing/weak article section: {need}'})
        if 'evidence:' not in txt and not rel.startswith('roles/'):
            rows.append({'severity':'warn','page':rel,'finding':'no cited claims'})
    if a.write_report:
        content='# Article Quality Lint\n\n'+('\n'.join(f"- **{r['severity']}** `{r['page']}` — {r['finding']}" for r in rows) if rows else '- PASS')+'\n'
        path=write_report(wiki,'article-quality-lint',content); append_log(wiki,'lint','article quality',[f'Wrote {path.relative_to(wiki).as_posix()} with {len(rows)} findings.'])
    emit(rows,a.format)
if __name__=='__main__': main()
