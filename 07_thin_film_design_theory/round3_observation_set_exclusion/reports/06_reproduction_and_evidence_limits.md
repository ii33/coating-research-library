# 06 · 离线复算、manifest与证据等级

## 6.1 文件结构和最小环境

README给出运行命令。models/set_exclusion.py是集合分类与标量绘图参考；run_tiny.py重算六个固定run；tests/test_reference.py执行有限guard、精确叶关系、决定性排除重放与点见证；validation_driver.py默认plan_only。光学与区间核及完整来源链是dependencies中的未改副本，85项字节hash由data/frozen_dependencies.json绑定。

核心复算仅依赖Python标准库。图重建另需matplotlib，reader里的PNG/SVG已预生成，阅读与验证不需它。HTML无远程资源、脚本或字体；原始Markdown和JSON可直接读取。无需安装依赖即可做reader校验与核心测试。

解压后先执行：python models/reader.py。再执行：PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v。重新生成tiny可执行：PYTHONDONTWRITEBYTECODE=1 python models/run_tiny.py。重算会覆盖verification/tiny_results.json中的运行时间，使冻结包校验不再匹配原hash；应在副本中运行，或将重算输出另存并比较逻辑字段。hash变化只表明字节不同，不自动意味着科学结果不同。

## 6.2 精确包边界

verification/reader_manifest.json列出每个发布载荷的相对路径、长度与SHA-256。它不列自己、压缩包、freeze/检查控制回执、sources/originals及本地原文归档回执。reader不仅校验列出的文件，也检查实际载荷文件集合，防止悄悄缺文件或多出未列文件。禁止symlink、路径逃逸、外部脚本及外部资源。

压缩包恰为manifest载荷加manifest本身。freeze_receipt在压缩包之外绑定archive的SHA-256与大小、manifest的SHA-256、实际成员数，以及独立解压、负向篡改、视觉QA等回执的hash。回执不把自己递归纳入其hash。最终final_receipt_check再次核对数字；没有上传或push。

论文原文只存在单独本地sources/originals，未进入reader、manifest或压缩包；来源登记只保存公共论文地址、使用范围和阅读证据，不保存账号、私有token或浏览器会话。原文版权仍属权利人，本包正文与图是原创推导/组织及数值结果，不能把公开可读等同于有权再分发全文。

## 6.3 tiny测试证明了什么

15个标准库测试包括：完整副本hash；M0原对象一致；来源正净资格；继承forward篡改拒绝；派生算子hash篡改拒绝；不支持背面拒绝；负净/跨零/近零/库存/非Lambert/状态guard；逐层单位与顺序；保存叶覆盖及分类关系；13节点决定性排除重放；三个点见证重放；预算必须保留UNKNOWN；全层乘积别名；T＝1−R约束冗余；外包络重叠不是实际交集的反例。

测试不是对任意输入的数学形式化证明。保留了与算法相同的包含核，独立光学核查才使用不同的特征矩阵路径。来源链的实际设备正确性、连续源认证和真实film状态均未被这些测试覆盖。

## 6.4 视觉与浏览器限制

三张原创图导出SVG及PNG，逐张查看实际PNG像素，检查标签、区间颜色、图例、边距和可读性。HTML只做结构检查：本地链接与锚点存在、没有远程资源或脚本、静态内容完整。继承的浏览器/headless/socket限制仍未解决；本轮不重复启动headless、不开放socket、不升级权限以绕过限制。因此HTML实际浏览器布局保持unverified，PNG检查不得写成HTML全通过。

## 6.5 复核与交付状态

作者检查完成后局部冻结，窄独立光学/单位检查只发生一次。正式模型链审查仍pending，point12仍partial，point2仍conditional non-strict。设备与heavy状态均为plan_only/not_run。只写本轮目录，冻结后的旧轮次、根计划与产品目录不变；outside_scope_check以启动前后项目文件hash比较验证这一点。

T08_ROUND3_HANDOFF.md只提供下一轮有限候选，不自动开始下一题。任何进一步实验、计划执行、远端发布或产品集成都需要单独明确任务。
