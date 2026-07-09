#!/usr/bin/env python
from __future__ import annotations
import argparse, re
from collections import Counter,defaultdict
from dwg_common import *
STOP=set('the and for with from that this are was were have has into about should would could when where after before using use not but its they their our your you'.split())
def terms(text):
    toks=[t.lower() for t in re.findall(r'[A-Za-z][A-Za-z0-9_/-]{3,}',text)]
    return [t for t in toks if t not in STOP and not t.isdigit()]
def main():
    ap=argparse.ArgumentParser(description='Find recurring topics/errors/configs that deserve new pages.'); ap.add_argument('--wiki',required=True); ap.add_argument('--db'); ap.add_argument('--min-records',type=int,default=3); ap.add_argument('--limit',type=int,default=50); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); conn=connect(db_path(wiki,a.db),readonly=True)
    existing={Path(r['page_path']).stem.replace('-',' ') for r in conn.execute('SELECT page_path FROM pages')}
    buckets=defaultdict(set); examples={}
    for r in conn.execute('SELECT case_id,data_type,normalized_text FROM data_points'):
        if r['data_type'] in {'error_or_boundary','command_or_config','config_key','version_or_upgrade_path'}:
            # exact-ish signature phrase
            phrase=' '.join(terms(r['normalized_text'])[:5])
            if phrase:
                buckets[(r['data_type'],phrase)].add(r['case_id']); examples.setdefault((r['data_type'],phrase),r['normalized_text'][:220])
        for t in terms(r['normalized_text']):
            if len(t)>5: buckets[('term',t)].add(r['case_id']); examples.setdefault(('term',t),r['normalized_text'][:220])
    out=[]
    for (typ,k),ids in buckets.items():
        if len(ids)>=a.min_records and not any(k.replace('_',' ') in e or e in k for e in existing):
            out.append({'candidate':k,'kind':typ,'record_count':len(ids),'example':examples[(typ,k)],'records':', '.join(sorted(ids)[:6])})
    out=sorted(out,key=lambda r:-r['record_count'])[:a.limit]; emit(out,a.format); conn.close()
if __name__=='__main__': main()
