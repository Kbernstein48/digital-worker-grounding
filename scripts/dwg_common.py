from __future__ import annotations

import csv, datetime, hashlib, html, json, os, re, sqlite3, subprocess, sys, zipfile
from pathlib import Path
from typing import Iterable, Sequence

CASE_COLS = ["case_id","source_ref","batch_id","ingested","status","case_type","topic","process_stage","root_cause","resolution_pattern","actors","systems","novel","pages_updated","gist","notes"]
DEFAULT_LIMIT = 50

SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS signatures;
DROP TABLE IF EXISTS source_artifacts;
DROP TABLE IF EXISTS claim_cases;
DROP TABLE IF EXISTS data_points;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS pages;
DROP TABLE IF EXISTS cases;
DROP VIEW IF EXISTS v_page_claim_counts;
DROP VIEW IF EXISTS v_data_point_counts;
CREATE TABLE cases (
  case_id TEXT PRIMARY KEY, source_ref TEXT, batch_id TEXT, ingested TEXT,
  status TEXT, case_type TEXT, topic TEXT, process_stage TEXT, root_cause TEXT,
  resolution_pattern TEXT, actors TEXT, systems TEXT, novel TEXT, pages_updated TEXT,
  gist TEXT, notes TEXT
);
CREATE TABLE pages (
  page_path TEXT PRIMARY KEY, title TEXT, type TEXT, updated TEXT, line_count INTEGER
);
CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY, page_path TEXT NOT NULL, heading TEXT, claim_text TEXT NOT NULL,
  evidence_count INTEGER, exemplar_case_ids TEXT, claim_kind TEXT,
  FOREIGN KEY(page_path) REFERENCES pages(page_path)
);
CREATE TABLE claim_cases (
  claim_id TEXT NOT NULL, case_id TEXT NOT NULL, support_type TEXT DEFAULT 'exemplar',
  PRIMARY KEY (claim_id, case_id), FOREIGN KEY(claim_id) REFERENCES claims(claim_id),
  FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE TABLE data_points (
  data_point_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, page_path TEXT, data_type TEXT NOT NULL,
  normalized_text TEXT NOT NULL, source_field TEXT, source_artifact TEXT, confidence TEXT DEFAULT 'medium',
  promoted_to_claim_id TEXT, FOREIGN KEY(case_id) REFERENCES cases(case_id),
  FOREIGN KEY(page_path) REFERENCES pages(page_path), FOREIGN KEY(promoted_to_claim_id) REFERENCES claims(claim_id)
);
CREATE TABLE signatures (
  signature_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, page_path TEXT, signature_type TEXT NOT NULL,
  normalized_signature TEXT NOT NULL, source_artifact TEXT, source_field TEXT, confidence TEXT DEFAULT 'medium',
  FOREIGN KEY(case_id) REFERENCES cases(case_id), FOREIGN KEY(page_path) REFERENCES pages(page_path)
);
CREATE TABLE source_artifacts (
  artifact_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, path TEXT NOT NULL, artifact_type TEXT,
  classification TEXT, extracted_chars INTEGER, data_point_count INTEGER DEFAULT 0, notes TEXT,
  FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE INDEX idx_data_points_case ON data_points(case_id);
CREATE INDEX idx_data_points_type ON data_points(data_type);
CREATE INDEX idx_data_points_page ON data_points(page_path);
CREATE INDEX idx_claims_page ON claims(page_path);
CREATE INDEX idx_claim_cases_case ON claim_cases(case_id);
CREATE INDEX idx_signatures_type ON signatures(signature_type);
CREATE INDEX idx_signatures_case ON signatures(case_id);
CREATE VIEW v_page_claim_counts AS
SELECT p.page_path, p.title, COUNT(c.claim_id) AS claim_count, COALESCE(SUM(c.evidence_count), 0) AS summed_evidence
FROM pages p LEFT JOIN claims c ON p.page_path = c.page_path GROUP BY p.page_path, p.title;
CREATE VIEW v_data_point_counts AS
SELECT data_type, COUNT(*) AS count, COUNT(DISTINCT case_id) AS record_count FROM data_points GROUP BY data_type;
"""

def today() -> str:
    return datetime.date.today().isoformat()

def stable_id(*parts) -> str:
    return hashlib.sha1("\u241f".join(str(p) for p in parts).encode('utf-8','ignore')).hexdigest()[:16]

def wiki_path(value: str|None=None) -> Path:
    return Path(value or os.environ.get('WIKI_PATH') or Path.home()/ 'wiki').expanduser().resolve()

def db_path(wiki: Path, db: str|None=None) -> Path:
    return Path(db).expanduser().resolve() if db else wiki/'_meta'/'knowledge.db'

def source_path(value: str|None=None) -> Path|None:
    return Path(value).expanduser().resolve() if value else None

def connect(db: Path, readonly=False) -> sqlite3.Connection:
    if readonly:
        if not db.exists(): raise SystemExit(f'knowledge DB not found: {db}')
        conn=sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True)
    else:
        db.parent.mkdir(parents=True, exist_ok=True); conn=sqlite3.connect(str(db))
    conn.row_factory=sqlite3.Row
    return conn

def clean_text(value) -> str:
    if value is None: return ''
    if not isinstance(value,str): value=str(value)
    value=html.unescape(value)
    value=re.sub(r'<(script|style)[^>]*>.*?</\1>',' ',value,flags=re.I|re.S)
    value=re.sub(r'v\\:\*\s*\{[^}]+\}|o\\:\*\s*\{[^}]+\}|w\\:\*\s*\{[^}]+\}|\.shape\s*\{[^}]+\}',' ',value,flags=re.I)
    value=re.sub(r'<br\s*/?>|</p>|</li>|</div>|</tr>|</h\d>',' ',value,flags=re.I)
    value=re.sub(r'<[^>]+>',' ',value)
    value=re.sub(r'\[~accountid:[^\]]+\]','<internal-mention>',value)
    value=re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','<email>',value)
    value=re.sub(r'https?://\S+','<url>',value)
    value=re.sub(r'\b(?:\+?\d[\s().-]?){8,}\b','<phone>',value)
    value=re.sub(r'\b[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+){2,}\b','<host>',value)
    value=re.sub(r'(Additional To:|Original Message|\bFrom:|\bSent:|\bBCC:|\bCC:|\bSubject:).*?(?=(Body:|$))',' ',value,flags=re.I|re.S)
    value=re.sub(r'\bBody:\s*',' ',value,flags=re.I)
    value=re.sub(r'If you (?:are not|have received|receive).*?(?:delete|destroy).*?\.',' ',value,flags=re.I)
    return re.sub(r'\s+',' ',value).strip()

def is_noise(text: str) -> bool:
    return bool(re.search(r'^(dear |hello |hi |thanks|regards|kind regards|from:|sent:|to:|cc:|subject:)|not the intended recipient|confidentiality|external email', text, re.I))

def split_chunks(text: str) -> list[str]:
    chunks=[]
    for part in re.split(r'[\r\n]+|\s+[•●]\s+|\s+\d+[.)]\s+', text):
        part=re.sub(r'\s+',' ',part).strip(' -–—*•\t')
        if not part: continue
        if len(part)>650:
            chunks.extend([x.strip() for x in re.split(r'(?<=[.!?])\s+',part) if x.strip()])
        else: chunks.append(part)
    return [x for x in chunks if 35 <= len(x) <= 900 and not is_noise(x)]

def classify_data_point(text: str) -> str:
    low=text.lower()
    if re.search(r'error|failed|exception|unable to|timeout|manifest_unknown|pkix|not supported|not recommended|access denied|unsupported', low): return 'error_or_boundary'
    if re.search(r'uipathctl|kubectl|helm|\bdocker\b|\bselect\b|\bupdate\b|cluster_config\.json|input\.json|versions\.json|\.ps1|\.sh|\.yaml|\.json', text, re.I): return 'command_or_config'
    if re.search(r'trustservercertificate|multi subnet failover|custom_dns_resolver|connectionstrings|resolv\.conf|keytab|kerberos|client_id|tenant', low): return 'config_key'
    if re.search(r'\b\d{2,4}\.\d+(?:\.\d+)?\b', text): return 'version_or_upgrade_path'
    if re.search(r'maintenance mode|backup|rollback|failover|failback|gslb|sql listener|snapshot|restore', low): return 'change_or_dr_control'
    if re.search(r'docs\.uipath|documentation|officially supported|guide|kb article', low): return 'documentation_reference'
    return 'observation'

def load_json(path: Path):
    try: return json.load(open(path, encoding='utf-8'))
    except Exception: return None

def rows_from_json(obj):
    if obj is None: return []
    if isinstance(obj, list): return obj
    if isinstance(obj, dict):
        for k in ('records','data','items','rows'):
            if isinstance(obj.get(k), list): return obj[k]
        return [obj]
    return []

def case_dir_from_source_ref(source_ref: str|None) -> Path|None:
    m=re.search(r'(C:\\.+)$', source_ref or '')
    if m: return Path(m.group(1))
    p=Path(source_ref or '')
    return p if str(source_ref or '').strip() and p.exists() else None

def load_ledger(wiki: Path) -> list[dict]:
    ledger=wiki/'_meta'/'ingest-ledger.csv'
    if not ledger.exists(): raise SystemExit(f'ledger not found: {ledger}')
    return list(csv.DictReader(open(ledger, encoding='utf-8')))

def page_meta(path: Path, wiki: Path):
    text=path.read_text(encoding='utf-8', errors='ignore')
    rel=path.relative_to(wiki).as_posix()
    title=path.stem.replace('-',' ').title(); typ='unknown'; updated=''
    if text.startswith('---'):
        end=text.find('\n---',3); fm=text[3:end] if end!=-1 else ''
        for line in fm.splitlines():
            if line.startswith('title:'): title=line.split(':',1)[1].strip().strip('"')
            elif line.startswith('type:'): typ=line.split(':',1)[1].strip()
            elif line.startswith('updated:'): updated=line.split(':',1)[1].strip()
    m=re.search(r'^#\s+(.+)$', text, re.M)
    if m: title=m.group(1).strip()
    return rel,title,typ,updated,len(text.splitlines()),text

def durable_pages(wiki: Path) -> list[Path]:
    out=[]
    for p in wiki.rglob('*.md'):
        parts=set(p.parts)
        if '_archive' in parts or '_meta' in parts: continue
        if p.name in {'SCHEMA.md','index.md','log.md'}: continue
        out.append(p)
    return sorted(out)

def infer_claim_kind(text: str, heading: str='') -> str:
    low=(heading+' '+text).lower()
    if re.search(r'error|failed|exception|unable|timeout|pkix|manifest_unknown|not supported|unsupported', low): return 'symptom_or_boundary'
    if re.search(r'uipathctl|kubectl|helm|command|config|connection string|cluster_config|prereq', low): return 'procedure_or_config'
    if re.search(r'must|should|boundary|supportability|not recommended|decision', low): return 'decision_rule'
    if re.search(r'evidence|source|field|artifact|ledger', low): return 'evidence_model'
    return 'article_claim'

def iter_claims(page_path: str, text: str):
    heading=''
    for raw in text.splitlines():
        line=raw.strip()
        if not line: continue
        hm=re.match(r'^(#{1,6})\s+(.+)$',line)
        if hm: heading=hm.group(2).strip(); continue
        if line.startswith('---') or re.match(r'^(title|created|updated|type|tags|exemplars|confidence|contested|rare-but-important):',line): continue
        if '(evidence:' not in line: continue
        claim=re.sub(r'^[-*]\s+','',line); claim=re.sub(r'^\d+\.\s+','',claim)
        em=re.search(r'\(evidence:\s*(\d+)\s+cases?\s+—\s+e\.g\.\s+([^\)]+)\)',claim)
        if not em: em=re.search(r'\(evidence:\s*(\d+)\s+cases?',claim)
        ev=int(em.group(1)) if em else None; exemplars=[]
        if em and em.lastindex and em.lastindex>=2:
            exemplars=[x.strip() for x in em.group(2).split(',') if x.strip()]
        ctext=re.sub(r'\s*\(evidence:[^\)]*\)','',claim).strip()
        yield stable_id(page_path,heading,ctext), heading, ctext, ev, ';'.join(exemplars), infer_claim_kind(ctext,heading), exemplars

def extract_text_from_file(path: Path) -> tuple[str,str]:
    ext=path.suffix.lower()
    try:
        if ext in {'.txt','.md','.log','.json','.csv','.yaml','.yml','.xml'}:
            return path.read_text(encoding='utf-8', errors='ignore'), 'text'
        if ext in {'.html','.htm'}:
            return clean_text(path.read_text(encoding='utf-8', errors='ignore')), 'html'
        if ext == '.docx':
            with zipfile.ZipFile(path) as z:
                text=' '.join(clean_text(z.read(n).decode('utf-8','ignore')) for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
            return text, 'docx'
        if ext == '.pdf':
            try:
                import fitz
                doc=fitz.open(str(path)); return '\n'.join(page.get_text() for page in doc), 'pdf'
            except Exception as e:
                return '', f'pdf-unreadable:{type(e).__name__}'
    except Exception as e:
        return '', f'unreadable:{type(e).__name__}'
    return '', 'unsupported'

def classify_artifact(path: Path, text: str, status: str) -> str:
    if status.startswith('unreadable') or status.startswith('pdf-unreadable'): return status
    if status=='unsupported': return 'unsupported'
    low=text.lower()
    if not text.strip(): return 'empty'
    if re.search(r'error|exception|failed|traceback|stack trace|uipathctl|kubectl|helm|manifest_unknown|pkix', low): return 'technical-evidence'
    if re.search(r'from:|sent:|subject:|regards|not the intended recipient|confidential', low): return 'email-or-boilerplate'
    if len(text)<80: return 'low-signal'
    return 'narrative-or-reference'

def extract_case_data_points(row: dict) -> list[tuple]:
    cid=row.get('case_id',''); d=case_dir_from_source_ref(row.get('source_ref'))
    points=[]
    def add(text, field, artifact):
        text=clean_text(text)
        for chunk in split_chunks(text):
            dtype=classify_data_point(chunk)
            if dtype=='observation' and not re.search(r'resolved|confirmed|configured|installed|upgraded|reviewed|recommended|validated|required|must|should|because', chunk, re.I): continue
            page=''
            pages=[p for p in (row.get('pages_updated') or '').split(';') if p.startswith(('concepts/','process/','playbooks/','governance/','automation/'))]
            if pages:
                page=pages[0]; low=chunk.lower()
                for p in pages:
                    toks=Path(p).stem.replace('-',' ').split()
                    if any(tok and tok in low for tok in toks[:4]): page=p; break
            points.append((cid,page,dtype,chunk,field,artifact))
    if d:
        case=load_json(d/'case.json') or {}
        for field in ['Problem__c','Cause__c','Solution__c','Subject','Purpose_of_Engagement__c','Deployment_Location__c','Environment_Of_Issue__c','AS_Deployment_Type__c']:
            if case.get(field): add(case.get(field), field, str(d/'case.json'))
        rel=d/'related'
        if rel.exists():
            for jp in rel.glob('*.json'):
                obj=load_json(jp)
                for item in rows_from_json(obj)[:80]:
                    if not isinstance(item,dict): continue
                    for k,v in item.items():
                        if isinstance(v,str) and k.lower() in {'body','textbody','htmlbody','commentbody','description','subject','title','summary'}:
                            add(v, f'related/{jp.stem}.{k}', str(jp))
    return points

def extract_signatures_from_text(text: str) -> list[tuple[str,str]]:
    sigs=[]
    patterns=[
      ('error', r'(?i)(?:error|exception|failed|unable to|access denied|timeout|manifest_unknown|PKIX|not supported)[^\n.;]{0,220}'),
      ('command', r'(?m)^\s*(?:uipathctl|kubectl|helm|docker|az|aws|gcloud|sqlcmd|openssl|curl)\b[^\n]{0,240}'),
      ('config_key', r'\b(?:trustServerCertificate|multi subnet failover|custom_dns_resolver|cluster_config\.json|input\.json|versions\.json|ConnectionStrings?|resolv\.conf|keytab)\b'),
      ('version', r'\b(?:20\d{2}|\d{2})\.\d+(?:\.\d+)?\b'),
      ('path', r'(?:[A-Za-z]:\\[^\s"\']+|/(?:etc|var|opt|home|tmp|mnt|uipath)[^\s"\']*)'),
    ]
    for typ,rx in patterns:
        for m in re.finditer(rx,text):
            s=clean_text(m.group(0)).strip(' :;-')
            if 3 <= len(s) <= 260: sigs.append((typ,s))
    return sigs

def emit(rows: Sequence[dict], fmt='table'):
    if fmt=='json': print(json.dumps(list(rows), indent=2, ensure_ascii=False)); return
    if fmt=='csv':
        rows=list(rows)
        if not rows: return
        w=csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()), lineterminator='\n'); w.writeheader(); w.writerows(rows); return
    rows=list(rows)
    if not rows: print('(no rows)'); return
    cols=list(rows[0].keys()); widths={c:min(max(len(c),*(len(str(r.get(c,''))) for r in rows[:100])),90) for c in cols}
    def cell(c,v):
        s=str(v if v is not None else '').replace('\n',' ')
        return s[:widths[c]-1]+'…' if len(s)>widths[c] else s
    print(' | '.join(c.ljust(widths[c]) for c in cols)); print('-+-'.join('-'*widths[c] for c in cols))
    for r in rows: print(' | '.join(cell(c,r.get(c)).ljust(widths[c]) for c in cols))

def append_log(wiki: Path, mode: str, scope: str, bullets: list[str]):
    with open(wiki/'log.md','a',encoding='utf-8') as f:
        f.write(f"\n## [{today()}] {mode} | {scope}\n")
        for b in bullets: f.write(f"- {b}\n")

def write_report(wiki: Path, name: str, content: str) -> Path:
    out=wiki/'_meta'/'audits'; out.mkdir(parents=True, exist_ok=True)
    path=out/f"{name}-{today()}.md"; path.write_text(content,encoding='utf-8'); return path
