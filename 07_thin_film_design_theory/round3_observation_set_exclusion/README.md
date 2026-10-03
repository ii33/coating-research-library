# T07 第三轮 · 有限观测集合排除

本轮新增：在同一六层合成膜系和有界公共厚度z下，检验原三节点MIR反射率与新增10 μm反射率，究竟能排除哪些有限层厚候选。

**结果**：H_outer10（最外层+10%）在原观测M0下有可行点，新增M1后整个先验z域被排除。H_global002（所有层×1.002）与z重参数化仍有精确层厚别名，无法独立归因到来源Q/ρ等。结论只针对绑定的有限合成模型及声明硬误差，不是实测、制造放行或全局唯一性。

打开 reader.html 阅读六篇原创工程报告、三张图、源登记和完整参考算法。报告依次讨论合同、来源资格、完整分支算法、结果、工程观测计划与复现限制。

## 离线命令

```bash
python models/reader.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
python models/validation_driver.py
# 在解压副本中重算tiny，会更新结果运行时间，不再匹配原冻结字节
PYTHONDONTWRITEBYTECODE=1 python models/run_tiny.py
# 可选，仅重建图需matplotlib
MPLCONFIGDIR=/tmp/t07-r3-mpl python models/build_figures_reader.py
```

核心仅用标准库；图已预生成，阅读不需安装任何包。正式heavy默认plan_only，没有设备、Monte Carlo或优化器执行。一次窄独立检查不替代正式模型链审查。point12 partial、point2 conditional non-strict与formal review pending维持不变。

原始文献在单独本地目录，不入reader载荷。HTML本地链接/静态结构已检，实际浏览器布局未验证；PNG像素逐张核看。此包仅local_freeze，无上传、push或启动T08。
