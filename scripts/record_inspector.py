#!/usr/bin/env python
from __future__ import annotations
import argparse
from dwg_common import *

def main():
    ap=argparse.ArgumentParser(description='Inspect one business record/case and show what it contributed.'); ap.add_argument('--wiki',required=True); ap.add_argument('record_id'); ap.add_argument('--db'); ap.add_argument('--limit',type=int,default=80); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); conn=connect(db_path(wiki,a.db),readonly=True); rid=a.record_id; rows=[]
    for r in conn.execute('SELECT * FROM cases WHERE case_id=?',(rid,)): rows.append({'section':'record','key':r['case_id'],'value':f"{r['status']} | {r['topic']} | {r['systems']} | {r['gist']}"})
    for r in conn.execute('SELECT page_path,data_type,source_field,substr(normalized_text,1,240) text FROM data_points WHERE case_id=? ORDER BY data_type,page_path LIMIT ?',(rid,a.limit)):
        rows.append({'section':'data_point','key':r['data_type'],'value':f"{r['page_path']} | {r['source_field']} | {r['text']}"})
    for r in conn.execute('SELECT c.page_path,c.heading,c.claim_kind,substr(c.claim_text,1,240) text FROM claim_cases cc JOIN claims c ON c.claim_id=cc.claim_id WHERE cc.case_id=? ORDER BY c.page_path LIMIT ?',(rid,a.limit)):
        rows.append({'section':'exemplar_claim','key':r['claim_kind'],'value':f"{r['page_path']} | {r['heading']} | {r['text']}"})
    for r in conn.execute('SELECT signature_type,normalized_signature,source_field FROM signatures WHERE case_id=? ORDER BY signature_type LIMIT ?',(rid,a.limit)):
        rows.append({'section':'signature','key':r['signature_type'],'value':f"{r['source_field']} | {r['normalized_signature']}"})
    emit(rows,a.format); conn.close()
if __name__=='__main__': main()
