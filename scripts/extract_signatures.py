#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from dwg_common import *

def main():
    ap=argparse.ArgumentParser(description='Extract exact errors, commands, config keys, versions, paths into DB signatures.'); ap.add_argument('--wiki',required=True); ap.add_argument('--db'); ap.add_argument('--limit-records',type=int); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); db=db_path(wiki,a.db); conn=connect(db); cur=conn.cursor()
    try: cur.execute('DELETE FROM signatures')
    except Exception: pass
    rows=load_ledger(wiki); count=0; seen=set()
    for row in rows[:a.limit_records or len(rows)]:
        for cid,page,dtype,text,field,artifact in extract_case_data_points(row):
            for stype,sig in extract_signatures_from_text(text):
                key=(cid,stype,sig,artifact)
                if key in seen: continue
                seen.add(key); cur.execute('INSERT OR IGNORE INTO signatures VALUES (?,?,?,?,?,?,?,?)',(stable_id(*key),cid,page,stype,sig,artifact,field,'medium')); count+=1
    conn.commit()
    summary=[dict(r) for r in conn.execute('SELECT signature_type,COUNT(*) count,COUNT(DISTINCT case_id) records FROM signatures GROUP BY signature_type ORDER BY count DESC')]
    append_log(wiki,'extract','signatures',[f'Refreshed signatures table with {count} signatures.'])
    emit(summary,a.format); conn.close()
if __name__=='__main__': main()
