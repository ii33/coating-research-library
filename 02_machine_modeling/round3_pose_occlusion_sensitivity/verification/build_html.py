"""Author-only local Pandoc rebuild; no browser, publication or remote assets."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
inputs=[R/'verification/reader_front.md']+sorted((R/'reports').glob('*.md'))+[R/'sources/research_notes.md',R/'reviews/INDEPENDENT_REVIEW.md',R/'reviews/AUTHOR_FIXES_AND_REPLAY.md',R/'T03_ROUND3_HANDOFF.md']
subprocess.run(['pandoc','--standalone','--embed-resources','--toc','--toc-depth=2',
    '--metadata','title=T02第三轮 机械位姿与硬遮挡敏感度','--metadata','lang=zh-CN',
    '--css',str(R/'verification/reader.css'),'--resource-path',str(R/'reports')+':'+str(R),
    *[str(p) for p in inputs],'-o',str(R/'reader.html')],check=True)
print('offline reader built; browser layout remains unverified')
