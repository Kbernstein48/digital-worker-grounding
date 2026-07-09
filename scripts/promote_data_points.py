#!/usr/bin/env python
from __future__ import annotations
import argparse, re
from collections import defaultdict
from dwg_common import *

def norm(t):
    t=re.sub(r'\d+','<n>',t.lower()); t=re.sub(r'[^a-z0-9_./ -]+',' ',t); return re.sub(r'\s+',' ',t).strip()[:120]

def main():
    ap=argparse.ArgumentParser(description='Find reusable data points that should become article claims.'); ap.add_argument('--wiki',required=True); ap.add_argument('--db'); ap.add_argument('--page'); ap.add_argument('--type'); ap.add_argument('--min-records',type=int,default=2); ap.add_argument('--limit',type=int,default=50); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); conn=connect(db_path(wiki,a.db),readonly=True)
    clauses=[]; params=[]
    if a.page: clauses.append('page_path LIKE ?'); params.append(f'%{a.page}%')
    if a.type: clauses.append('data_type=?'); params.append(a.type)
    where='WHERE '+' AND '.join(clauses) if clauses else ''
    groups=defaultdict(lambda:{'records':set(),'examples':[],'page':'','type':''})
    for r in conn.execute(f'SELECT case_id,page_path,data_type,normalized_text FROM data_points {where}', params):
        key=(r['page_path'],r['data_type'],norm(r['normalized_text']))
        g=groups[key]; g['records'].add(r['case_id']); g['page']=r['page_path']; g['type']=r['data_type']
        if len(g['examples'])<3: g['examples'].append(r['normalized_text'][:220])
    out=[]
    for (_,_,k),g in groups.items():
        if len(g['records'])>=a.min_records:
            out.append({'page_path':g['page'],'data_type':g['type'],'record_count':len(g['records']),'candidate_claim':g['examples'][0],'exemplar_records':', '.join(sorted(g['records'])[:5])})
    out=sorted(out,key=lambda r:(-r['record_count'],r['page_path']))[:a.limit]
    emit(out,a.format); conn.close()
if __name__=='__main__': main()
