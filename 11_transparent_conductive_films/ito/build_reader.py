"""Build an offline reader from original research chapters; pandoc is author-only."""
from pathlib import Path
import re,subprocess,tempfile
root=Path(__file__).resolve().parent
files=['README.md','process/report.md','integration/01_flux_material_state.md',
'electro_optics/report.md','integration/04_synthetic_visual.md','integration/02_calibration_validation.md',
'integration/03_engineering_foundations.md','sources/README.md','process/fulltext_gaps.md',
'electro_optics/source_ledger.md','verification/independent_review.md']
parts=['---\ntitle: ITO 透明导电膜\nsubtitle: 从蒸镀工艺到仿真模型 阶段一研究\ndate: 2026年10月3日\nlang: zh-CN\n---\n\n![源通量与材料状态分层研究链](integration/pipeline.svg)\n']
for rel in files:
    path=root/rel
    if not path.exists():
        if rel=='process/fulltext_gaps.md': continue
        raise FileNotFoundError(path)
    text=path.read_text()
    def rewrite(m):
        label,url=m.group(1),m.group(2)
        if ':' in url or url.startswith('#'):return m.group(0)
        return '['+label+']('+str(path.parent.relative_to(root)/url)+')'
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',rewrite,text)
    parts.append(text)
with tempfile.TemporaryDirectory() as t:
    f=Path(t)/'reader.md';f.write_text('\n\n'.join(parts))
    subprocess.run(['pandoc',str(f),'-s','--toc','--toc-depth=2','--self-contained','--resource-path='+str(root),
                    '--css='+str(root/'report_style.css'),'-o',str(root/'ITO研究报告.html')],check=True)
print(root/'ITO研究报告.html')
