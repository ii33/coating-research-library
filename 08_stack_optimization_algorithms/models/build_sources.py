#!/usr/bin/env python3
"""Write original summary cards; source access was checked 2026-10-02."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
rows=[
('O01','least_squares','SciPy developers','1.17.0','https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html','official_solver_documentation','API, options, termination and method notes','jac, bounds, method, x_scale, max_nfev, nfev','有界非线性最小二乘使用TRF；LM不支持边界；数值差分调用不计入nfev。','API与本地1.17.0一致；文档的成功退出不等于用户光谱达标。','O01_scipy_least_squares.html'),
('O02','minimize(method=L-BFGS-B)','SciPy developers','1.17.0','https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.minimize-lbfgsb.html','official_solver_documentation','Options and termination','ftol, gtol, maxfun, maxiter, maxcor','盒约束标量目标可用有限记忆拟牛顿；投影梯度与函数变化决定停止。','不直接处理总厚度一般线性约束；梯度正确仍没有非凸全局最优保证。',None),
('O03','differential_evolution','SciPy developers','1.17.0','https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.differential_evolution.html','official_solver_documentation','API and budget/options','popsize, maxiter, rng, polish, updating','有界群体搜索可提供多样起点；固定随机种子和关闭隐式polish使预算可追溯。','有限群体/代数不构成全局最优证书，不能把方法标签当结果保证。',None),
('O04','minimize(method=SLSQP)','SciPy developers','online 1.18; local solver1.17','https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html','official_solver_documentation','API and constraint/termination notes','ftol, constraints, multipliers','顺序二次规划支持厚度上限等显式约束；应独立核验最终违例。','网页默认版本与本地版本不同；本册仅用1.17已存在的基础接口，无新版本特性依赖。',None),
('O05','Application of the needle optimization technique to the design of optical coatings','A. V. Tikhonravov; M. K. Trubetskov; G. W. DeBell','1996, AO35:5493–5508','https://opg.optica.org/ao/abstract.cfm?uri=ao-35-28-5493','primary_paper','Publisher abstract and bibliographic record only','DOI10.1364/AO.35.005493','needle通过材料局部插入改变层结构，和已有层厚度精修形成互补。','全文订阅访问未取得；具体插入推导由本册独立实现并参照O07作者公开章节。',None),
('O06','Optical coating design approaches based on the needle optimization technique','A. V. Tikhonravov; M. K. Trubetskov; G. W. DeBell','2007, AO46:704–710','https://opg.optica.org/ao/abstract.cfm?uri=ao-46-5-704','primary_paper','Publisher abstract and record','DOI10.1364/AO.46.000704','保留性能、层数、总光学厚度不同的设计集合，便于制造取舍；可存在近似等效多解。','没有复现文中层表或性能；物理总厚度与参考波长光学厚度不可混同。',None),
('O07','Basics of Optics of Multilayer Systems: selected chapters','Sh. A. Furman; A. V. Tikhonravov','1992, author-site selection','https://optilayer.com/content/book_Furm_Tikh.pdf','primary_author_textbook','Selected optimization and needle sections read from full public PDF','printed pp98–125; §§2.1–2.2; Eq2.1.5,2.1.14,2.1.19','误差积分离散、梯度、材料needle变分和删层构成相互衔接的综合流程。','原文符号约定需转换；书中小层数经验不当作本项目全局最优证明。','O07_furman_selected_chapters.pdf'),
('O08','TMM-Fast: A Transfer Matrix Computation Package for Multilayer Thin-Film Optimization','Alexander Luce; Ali Mahdavi; Florian Marquardt; Heribert Wankerl','2021 v1','https://arxiv.org/abs/2111.13667','primary_author_paper','Full public PDF, focus §§1,3–6','arXiv2111.13667; parallel wavelength/angle and torch gradients','向量化与自动微分可降低多层计算和局部优化成本，亦可生成训练数据。','未安装/运行该包，不能继承其速度倍数；本册坚持稳定S核，未把大M连乘当普遍稳定方案。','O08_tmm_fast.pdf'),
('O09','tmm_fast author repository','MLResearchAtOSRAM; Alexander Luce et al.','retrieved2026-10-02','https://github.com/MLResearchAtOSRAM/tmm_fast','primary_author_software','README and license metadata','repository overview, MIT code license','提供可追踪的并行/自动微分实现入口，供后续对照和性能迁移。','本轮不执行外部代码、不克隆未锁定主分支；论文与代码的许可证分别判断。',None),
('O10','OL-Transformer: A Fast and Universal Surrogate Simulator for Optical Multilayer Thin Film Structures','Taigao Ma; Haozhu Wang; L. Jay Guo','2023; arXiv v2','https://arxiv.org/html/2305.11984v2','primary_author_paper','Full HTML, architecture and error discussions','arXiv2305.11984; simulation and transfer-learning sections','代理可近似正问题并支持反设计；训练分布和迁移条件决定泛化范围。','本册未训练Transformer、不采用论文速度作为自有证据；离域和尖锐窄带响应仍需精确回证。',None),
('O11','Global Convergence of General Derivative-Free Trust-Region Algorithms to First and Second Order Critical Points','Andrew R. Conn; Katya Scheinberg; Luis N. Vicente','2006 preprint06-49','https://optimization-online.org/2006/10/1504/','primary_methods_paper','Public PDF abstract, assumptions and trust-region framework','PDF pp1–8; Taylor-type model bounds and criticality','可信局部代理需模型误差与半径控制；全局收敛语境是趋于驻点而不是全局最小。','本册示例只做线性模型实际下降回证，未实现完整模型质量/临界性机制，不能移植定理。',None),
('O12','Correlation of errors in optical coating production with broad band monitoring','A. V. Tikhonravov; I. V. Kochikov; I. A. Matvienko et al.','2018','https://en.num-meth.ru/index.php/journal/article/view/986','primary_methods_paper','Official abstract; existing authorized CC BY4.0 PDF; selective read','DOI10.26089/NumMet.v19r439; abstract, statistical model','光学监控可使层误差相关；情景分布必须和监控模型、统计证据匹配。','本册共模+独立高斯是人为压力情景，不是该论文拟合，也不是本机良率。','O12_error_correlation_2018.pdf'),
('O13','Multilayer optical calculations','Steven J. Byrnes','2016; v5','https://arxiv.org/abs/1603.02720','primary_author_methods','Existing public v5 PDF; conventions, absorption and branch sections','§§2–6 and appendices','复折射率、功率归一化和吸收端口边界是优化前必须确定的物理契约。','本册切向p振幅约定自成一体；材料实测和整窗响应不由公式自动提供。','O13_byrnes_v5.pdf'),
('O14','Improved Formulation of Scattering Matrices for Semi-Analytical Methods That Is Consistent with Convention','Raymond C. Rumpf','2011','https://www.jpier.org/PIERB/pier.php?paper=11083107','primary_methods_paper','Publisher record and existing PDF cascade sections','DOI10.2528/PIERB11083107; PIERB35:241–261','端口定义和散射级联提供稳定分层计算的表示基础。','本册标量星積和厚度导数自行推导；未声称实现论文一般多模求解器。','O14_rumpf_2011.pdf'),
('O15','Efficient optimization of multilayer coatings for ultrafast optics using analytic gradients of dispersion','Jonathan R. Birge; Franz X. Kärtner','2007','https://opg.optica.org/ao/abstract.cfm?uri=ao-46-14-2656','primary_methods_paper','Publisher/search abstract and bibliographic metadata only','DOI10.1364/AO.46.002656','相位色散梯度可被解析计算并用于薄膜优化，说明功率目标并非唯一需求。','本轮没有相位/GD/GDD优化数值验证，不把论文的线性层数复杂度转为自有实测。',None),
('O16','Autograd mechanics: complex numbers','PyTorch developers','online documentation; retrieved2026-10-02','https://docs.pytorch.org/docs/stable/notes/autograd.html','official_framework_documentation','Complex differentiation and real-loss conventions','Autograd for Complex Numbers','复数内部运算与实标量损失需采用一致实/Wirtinger微分约定。','本册没有调用PyTorch，手写切线不能表述为已做框架AD三方验证。',None)
]
sources=[]
for sid,title,authors,year,url,kind,read,loc,summary,limit,local in rows:
    if local and not (ROOT/'sources/originals'/local).exists():local=None
    item=dict(id=sid,title=title,authors=authors,year=year,url=url,source_type=kind,checked_on='2026-10-02',read_extent=read,locator=loc,summary=summary,limitations=limit,summary_path=f'sources/summaries/{sid}.md',local_original=local,original_archival_status='authorized public copy for local research; excluded from public package' if local else 'link and original summary; no local full text claimed')
    if local:
        f=ROOT/'sources/originals'/local;item.update(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size)
    if sid=='O08':item['rights']='Paper CC BY-SA4.0 per arXiv license link; code separately MIT'
    if sid=='O12':item['rights']='CC BY4.0 per publisher'
    sources.append(item)
    (ROOT/item['summary_path']).write_text(f'''# {sid} · {title}

- 作者/机构：{authors}
- 年份/版本：{year}
- 来源：[{title}]({url})
- 证据类型：{kind}
- 核验日期：2026-10-02
- 实际读取：{read}
- 定位：{loc}

## 原创摘要

{summary}

## 使用限制

{limit}

## 原文状态

{item['original_archival_status']}。公开能读不等于公开再分发许可。原文/提取文本只在本地排除目录；公开包含原创摘要、来源链接与自有代码结果。
''')
(ROOT/'data/source_registry.json').write_text(json.dumps(dict(schema_version='1.0',sources=sources),ensure_ascii=False,indent=2)+'\n')
print(len(sources),'source cards',sum(bool(s['local_original']) for s in sources),'local originals')
