#!/usr/bin/env python
from __future__ import annotations
import argparse, os
from pathlib import Path
from dwg_common import *

def main():
    ap=argparse.ArgumentParser(description='Parse HTML/TXT/MD/PDF/DOCX/log attachments into sanitized data points.'); ap.add_argument('--wiki',required=True); ap.add_argument('--source',required=False); ap.add_argument('--db'); ap.add_argument('--limit-files',type=int); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); wiki=wiki_path(a.wiki); db=db_path(wiki,a.db); conn=connect(db); cur=conn.cursor(); rows=load_ledger(wiki)
    source = Path(a.source).expanduser().resolve() if a.source else None
    processed=0; dp_count=0; artifacts=0
    for row in rows:
        cid=row['case_id']; d=case_dir_from_source_ref(row.get('source_ref'))
        if not d or not d.exists(): continue
        for root,dirs,files in os.walk(d):
            if '__MACOSX' in root: continue
            for fn in files:
                p=Path(root)/fn
                if p.suffix.lower() not in {'.html','.htm','.txt','.md','.log','.json','.pdf','.docx'}: continue
                if a.limit_files and processed>=a.limit_files: break
                text,status=extract_text_from_file(p); classification=classify_artifact(p,text,status); processed+=1
                art_id=stable_id(cid,str(p)); local_dp=0
                if classification in {'technical-evidence','narrative-or-reference'}:
                    for chunk in split_chunks(clean_text(text))[:20]:
                        dtype=classify_data_point(chunk)
                        if dtype=='observation' and classification!='technical-evidence': continue
                        page=''
                        pages=[x for x in (row.get('pages_updated') or '').split(';') if x.startswith('concepts/')]
                        if pages: page=pages[0]
                        cur.execute('INSERT OR REPLACE INTO data_points VALUES (?,?,?,?,?,?,?,?,?)',(stable_id(cid,dtype,chunk,str(p)),cid,page,dtype,chunk,'attachment',str(p),'medium',None)); dp_count+=1; local_dp+=1
                        for stype,sig in extract_signatures_from_text(chunk):
                            cur.execute('INSERT OR IGNORE INTO signatures VALUES (?,?,?,?,?,?,?,?)',(stable_id(cid,stype,sig,str(p)),cid,page,stype,sig,str(p),'attachment','medium'))
                cur.execute('INSERT OR REPLACE INTO source_artifacts VALUES (?,?,?,?,?,?,?,?)',(art_id,cid,str(p),p.suffix.lower(),classification,len(text),local_dp,'')); artifacts+=1
            if a.limit_files and processed>=a.limit_files: break
        if a.limit_files and processed>=a.limit_files: break
    conn.commit(); out=[dict(r) for r in conn.execute('SELECT classification,COUNT(*) artifacts,SUM(data_point_count) data_points FROM source_artifacts GROUP BY classification ORDER BY artifacts DESC')]
    append_log(wiki,'ingest','attachments',[f'Parsed {artifacts} artifacts; added/updated {dp_count} data points.'])
    emit(out,a.format); conn.close()
if __name__=='__main__': main()
