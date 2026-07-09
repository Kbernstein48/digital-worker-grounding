#!/usr/bin/env python
from __future__ import annotations
import argparse, re
from pathlib import Path
from dwg_common import *

def audit(wiki: Path, db: Path):
    conn=connect(db, readonly=True); findings=[]
    def add(sev,kind,msg,ref='',count=None): findings.append({'severity':sev,'kind':kind,'message':msg,'ref':ref,'count':count})
    q=lambda s,*p: conn.execute(s,p).fetchall()
    for r in q('SELECT COUNT(*) n FROM claim_cases cc LEFT JOIN claims c ON c.claim_id=cc.claim_id LEFT JOIN cases ca ON ca.case_id=cc.case_id WHERE c.claim_id IS NULL OR ca.case_id IS NULL'):
        if r['n']: add('error','orphan_claim_cases','Claim-case links point to missing claims or records',count=r['n'])
    for r in q('SELECT COUNT(*) n FROM data_points dp LEFT JOIN cases ca ON ca.case_id=dp.case_id LEFT JOIN pages p ON p.page_path=dp.page_path WHERE ca.case_id IS NULL OR (dp.page_path IS NOT NULL AND dp.page_path != "" AND p.page_path IS NULL)'):
        if r['n']: add('error','orphan_data_points','Data points point to missing records or pages',count=r['n'])
    for r in q('SELECT claim_id,page_path,substr(claim_text,1,160) txt FROM claims WHERE evidence_count>0 AND (exemplar_case_ids IS NULL OR exemplar_case_ids="") LIMIT 100'):
        add('warn','claim_without_exemplar','Claim has evidence count but no exemplar IDs',r['page_path']+'#'+r['claim_id'])
    for r in q('SELECT p.page_path,p.title,COUNT(dp.data_point_id) dps,COUNT(c.claim_id) claims FROM pages p LEFT JOIN data_points dp ON dp.page_path=p.page_path LEFT JOIN claims c ON c.page_path=p.page_path GROUP BY p.page_path HAVING claims>20 AND dps=0 LIMIT 100'):
        add('warn','page_claims_no_data_points','Page has many claims but no mapped data points',r['page_path'],r['claims'])
    for r in q('SELECT case_id,gist FROM cases WHERE (pages_updated IS NULL OR pages_updated="") AND status="ok" LIMIT 100'):
        add('warn','record_no_pages','Record is ok but updated no pages',r['case_id'])
    for r in q('SELECT case_id,COUNT(*) n FROM data_points GROUP BY case_id HAVING n>=5 AND case_id NOT IN (SELECT DISTINCT case_id FROM claim_cases) LIMIT 100'):
        add('info','rich_record_not_exemplar','Record has many data points but is not an exemplar for any claim',r['case_id'],r['n'])
    for p in durable_pages(wiki):
        txt=p.read_text(encoding='utf-8',errors='ignore')
        if re.search(r'Additional To:|Original Message|\bFrom:|\bSent:|not the intended recipient|<email>|<phone>|\.\.\.|Body:',txt,re.I):
            add('error','source_fragment','Page contains raw-source or truncation artifact',p.relative_to(wiki).as_posix())
    report=['# Evidence Audit','']
    for f in findings: report.append(f"- **{f['severity']} / {f['kind']}** `{f.get('ref','')}` {f['message']}"+(f" ({f['count']})" if f.get('count') is not None else ''))
    if not findings: report.append('- PASS: no findings.')
    path=write_report(wiki,'evidence-audit','\n'.join(report)+'\n')
    append_log(wiki,'audit','evidence',[f'Wrote {path.relative_to(wiki).as_posix()} with {len(findings)} findings.'])
    conn.close(); return findings,path

def main():
    ap=argparse.ArgumentParser(description='Check claims, citations, data points, orphan records, and weak evidence.'); ap.add_argument('--wiki',required=True); ap.add_argument('--db'); ap.add_argument('--format',choices=['table','json','csv'],default='table')
    a=ap.parse_args(); findings,path=audit(wiki_path(a.wiki), db_path(wiki_path(a.wiki),a.db)); emit(findings,a.format); print(f'\nreport: {path}')
if __name__=='__main__': main()
