import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
base=json.loads((P/'data/standards_map_base.json').read_text())
reg=json.loads((P/'data/source_registry.json').read_text())
reg['sources']=[s for s in reg['sources'] if not s['source_id'].startswith('T09-MG')]
extra=json.loads((P/'data/official_status_mil_gb.json').read_text())
allstd=base['standards'].copy()
for i,r in enumerate(extra['standards'],1):
 sid=f'T09-MG{i:03d}'
 src=dict(source_id=sid,identity=r['id'],publisher='DLA ASSIST' if r['family']=='MIL' else 'SAMR/SAC',url=r['url'],accessed_date=extra['query_date'],evidence_level='A',claim_status='reported',official_status=r['status'],date_value=r['publication_date'],implementation_date=r.get('implementation_date'),role='catalogue_mapping',summary=r['evidence_summary'],locator='official catalogue/status/history/adoption fields',full_text_reviewed=False,normative_clause_verified=False,original_archived=False,redistribution_allowed=False,summary_redistribution_allowed=True,limitations=r.get('access_limitation',r.get('limitation',r['verification_scope'])),summary_path='sources/summaries/official_status_mil_gb.md')
 reg['sources'].append(src)
 st=src.copy();st['official_record']=r;st['adoption']=r.get('adoption');allstd.append(st)
for s in allstd:
 s['standard_id']=s['identity']
 s['clause_mapping_status']='not_ready_for_conformity_statement'
 s['normative_clause']=None
 s['severity']=None
 s['acceptance_threshold']=None
 s['sampling_plan']=None
 s['contract_selected']=False
 s['laboratory_evidence']=None
out=dict(version='T09-r1-v0.1.0',as_of_date='2026-10-02',query_not_guarantee_of_live_source_date=True,contract_ready=False,real_compliance_statement=False,standards=allstd,gaps=extra['verification_gaps'],notes=['Published is not contract adoption; ISO stage to be revised is not Withdrawn','GB forthcoming date is distinct from effective date','DLA Inactive for New Design differs from Canceled','Scope/abstract read does not verify complete normative procedure'])
(P/'data/standards_map.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(P/'data/source_registry.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
lines=['# 官方来源与研究参考索引','', '查询日期2026-10-02。以下为身份/链接及原创摘要索引；无第三方全文归档。目录缓存限制、版次差异和适用条件见每份摘要及标准主表。', '', '| ID | 文件或来源 | 原创摘要 |','|---|---|---|']
for s in reg['sources']:
 lines.append(f"| {s['source_id']} | [{s['identity']}]({s['url']}) | [摘要](../{s['summary_path']}) |")
(P/'reports/00_source_index.md').write_text('\n'.join(lines)+'\n')
conflicts=[
 dict(id='CF01',subject='ISO committee catalogue cache versus item stage',evidence=['https://www.iso.org/committee/53700/x/catalogue/','https://www.iso.org/standard/80475.html'],observation='9211-7 catalogue cached 90.20; product page 90.60 with dated 2026-09-03 close of review; other search cache showed later draft stage than cached opened catalogue',resolution='record product page Published +90.60; do not convert review stage to withdrawal'),
 dict(id='CF02',subject='ASTM B117 search cache versus current explicit page',evidence=['https://store.astm.org/standards/b117','https://store.astm.org/b0117-26a.html'],observation='search result initially showed B117-26; current explicit version and live family page showed B117-26a Active last updated 2026-09-22',resolution='use B117-26a current page, retain historical search discrepancy'),
 dict(id='CF03',subject='ISO publication month versus lifecycle publication day',evidence=['https://www.iso.org/standard/43004.html','https://www.iso.org/standard/66490.html'],observation='catalogue publication month can differ from dated stage60.60 event, e.g. TR21254-4 publication month 2011-09 versus lifecycle 2011-08-25',resolution='do not conflate; no inferred global mandatory implementation date')]
for r in extra['standards']:
 if r.get('conflicts'):
  conflicts.append(dict(id=f'CF{len(conflicts)+1:02d}',subject=r['id'],evidence=[r['url']]+[q['url'] for q in r.get('additional_sources',[])],observation=r['conflicts'],resolution='preserved as in official_status_mil_gb.json; no inferred correction'))
(P/'reviews/source_conflicts.json').write_text(json.dumps(dict(as_of='2026-10-02',conflicts=conflicts),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sources':len(reg['sources']),'standard_records':len(allstd),'conflicts':len(conflicts)}))
