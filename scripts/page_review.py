#!/usr/bin/env python
from __future__ import annotations
import argparse, re
from pathlib import Path
from dwg_common import *

def main():
    ap=argparse.ArgumentParser(description='Review one wiki page: claims, supporting records, gaps, split/merge suggestions.')
    ap.add_argument('--wiki',required=True); ap.add_argument('page'); ap.add_argument('--db'); ap.add_argument('--limit',type=int,default=30); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); conn=connect(db_path(wiki,a.db),readonly=True); page=a.page
    if not page.endswith('.md') and not page.startswith(('concepts/','process/','automation/','playbooks/','governance/','evaluations/','roles/')):
        page='concepts/'+page+'.md'
    rows=[]
    meta=conn.execute('SELECT *, (SELECT COUNT(*) FROM claims WHERE page_path=pages.page_path) claim_count, (SELECT COUNT(*) FROM data_points WHERE page_path=pages.page_path) data_point_count FROM pages WHERE page_path=? OR page_path LIKE ?', (page,f'%{page}%')).fetchall()
    for m in meta: rows.append({'section':'page','key':m['page_path'],'value':f"{m['title']} | claims={m['claim_count']} data_points={m['data_point_count']} lines={m['line_count']}"})
    claims=conn.execute('SELECT claim_id,heading,claim_kind,evidence_count,exemplar_case_ids,claim_text FROM claims WHERE page_path=? ORDER BY evidence_count DESC LIMIT ?', (page,a.limit)).fetchall()
    for c in claims: rows.append({'section':'claim','key':c['claim_kind'],'value':f"{c['evidence_count']} | {c['heading']} | {c['claim_text'][:220]}"})
    dps=conn.execute('SELECT data_type,case_id,source_field,normalized_text FROM data_points WHERE page_path=? ORDER BY data_type,case_id LIMIT ?', (page,a.limit)).fetchall()
    for d in dps: rows.append({'section':'data_point','key':d['data_type'],'value':f"{d['case_id']} {d['source_field']}: {d['normalized_text'][:220]}"})
    # simple gaps/suggestions
    txt=(wiki/page).read_text(encoding='utf-8',errors='ignore') if (wiki/page).exists() else ''
    for need in ['Scope','Diagnosis','workflow','Boundaries','Related']:
        if need.lower() not in txt.lower(): rows.append({'section':'gap','key':need,'value':'Missing or weak standard article section.'})
    type_counts=conn.execute('SELECT data_type,COUNT(*) n FROM data_points WHERE page_path=? GROUP BY data_type ORDER BY n DESC',(page,)).fetchall()
    for t in type_counts:
        if t['n']>=10: rows.append({'section':'suggestion','key':'expand_or_split','value':f"{t['n']} {t['data_type']} data points may deserve a named pattern/subsection."})
    emit(rows,a.format); conn.close()
if __name__=='__main__': main()
