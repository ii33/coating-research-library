"""Author-only Pandoc rebuild. Does not open a browser or publish."""
from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1]
inputs=[R/'verification/reader_front.md']+sorted((R/'reports').glob('*.md'))+[R/'sources/research_notes.md',R/'reviews/INDEPENDENT_REVIEW.md',R/'reviews/AUTHOR_FIXES_AND_REPLAY.md',R/'T02_ROUND3_HANDOFF.md']
subprocess.run(['pandoc','--standalone','--embed-resources','--toc','--toc-depth=2','--metadata','title=T01第三轮 行星机构机械误差与可观测校准','--metadata','lang=zh-CN','--css',str(R/'verification/reader.css'),'--resource-path',str(R/'verification')+':'+str(R),*[str(p) for p in inputs],'-o',str(R/'reader.html')],check=True)
print('reader.html built locally; browser layout unverified')
