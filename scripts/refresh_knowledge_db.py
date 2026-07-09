#!/usr/bin/env python
from __future__ import annotations
import argparse, json
from pathlib import Path
from dwg_common import *

def refresh(wiki: Path, db: Path) -> dict:
    rows=load_ledger(wiki)
    if db.exists(): db.unlink()
    conn=connect(db); conn.executescript(SCHEMA_SQL); cur=conn.cursor()
    for r in rows:
        cur.execute('INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',[r.get(c,'') for c in CASE_COLS])
    for p in durable_pages(wiki):
        rel,title,typ,updated,line_count,text=page_meta(p,wiki)
        cur.execute('INSERT INTO pages VALUES (?,?,?,?,?)',(rel,title,typ,updated,line_count))
        for cid,heading,ctext,ev,exs,kind,exlist in iter_claims(rel,text):
            cur.execute('INSERT OR REPLACE INTO claims VALUES (?,?,?,?,?,?,?)',(cid,rel,heading,ctext,ev,exs,kind))
            for case_id in exlist:
                cur.execute('INSERT OR IGNORE INTO claim_cases VALUES (?,?,?)',(cid,case_id,'exemplar'))
    seen=set(); dp_count=0
    for r in rows:
        per={}
        for case_id,page,dtype,text,field,artifact in extract_case_data_points(r):
            key=(case_id,dtype,text.lower()[:240])
            if key in seen: continue
            seen.add(key); per[dtype]=per.get(dtype,0)+1
            if per[dtype]>12: continue
            cur.execute('INSERT OR REPLACE INTO data_points VALUES (?,?,?,?,?,?,?,?,?)',(stable_id(case_id,dtype,text,field),case_id,page,dtype,text,field,artifact,'medium',None)); dp_count+=1
            for stype,sig in extract_signatures_from_text(text):
                cur.execute('INSERT OR IGNORE INTO signatures VALUES (?,?,?,?,?,?,?,?)',(stable_id(case_id,stype,sig,artifact),case_id,page,stype,sig,artifact,field,'medium'))
    conn.commit()
    summary={t:cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['cases','pages','claims','claim_cases','data_points','signatures','source_artifacts']}
    conn.close(); append_log(wiki,'index','knowledge DB refresh',[f"Refreshed `_meta/knowledge.db`: {summary}."])
    return {'db':str(db), **summary}

def main():
    ap=argparse.ArgumentParser(description='Rebuild _meta/knowledge.db from ledger, pages, and source records.')
    ap.add_argument('--wiki', required=True); ap.add_argument('--db') ; ap.add_argument('--format',choices=['json','table'],default='json')
    args=ap.parse_args(); wiki=wiki_path(args.wiki); out=refresh(wiki, db_path(wiki,args.db)); print(json.dumps(out,indent=2) if args.format=='json' else out)
if __name__=='__main__': main()
