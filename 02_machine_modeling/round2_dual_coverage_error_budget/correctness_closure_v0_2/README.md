# T02 v0.2 有限求交正确性闭环

2026-10-02 UTC。**原极近侧壁漏挡已在独立参考求交模块闭合；完整T02源/时间模型仍是有限数值未全通过。** 本目录不覆盖或重新发布父目录v0.1，不进入T03。

## 最重要的变化

- 方向不再与固定1e−14 m阈值比较。对给定存储数值采用标准库有理判定，原反例由旧 clear 改为 blocked，并与独立六面 oracle 相符
- `blocked / clear / unknown` 三态明确区分名义确定几何与给定局部不确定界。unknown不允许强制转bool，且不能静默透明
- 8,265组名义几何比较零差异，另有256扰动见证；一次独立复核发现两个API验证缺陷，修复后保留初始失败与有限复看记录
- 原0.203%源求积族差、14.3 ms独曝时长差和partial状态完整保留。本修复没有重跑或提高源/时间网格

## 阅读顺序

1. [原理、数值范围及公共API](reports/01_predicate_and_api.md)
2. [有限结果、残余边界及oracle使用限制](reports/02_results_and_boundaries.md)
3. [一次独立复核及修复证据](reviews/INDEPENDENT_REVIEW.md)
4. [预登记的测试与停止条件](verification/PRE_REGISTERED_PROTOCOL.md)
5. [机器结果](data/check_results.json)、[累计资源](verification/execution_ledger.json)、[父版本来源哈希](data/legacy_provenance.json)

## 独立复算与校验

仅Python 3.10+标准库，无NumPy、原项目、父目录、第三方原件或ZIP依赖。工作目录为本README所在目录：

```sh
python -B verification/run_checks.py
python -B verification/reader_check.py --check --reader
```

主套件默认只读。独立脚本会写入并覆盖同目录的independent_results.json；若需重新运行，请只在临时副本中执行`python -B reviews/independent_review.py`，不要在冻结目录覆盖初始失败和最终复看历史。其重跑不是完整性验证。发布者使用`python -B verification/reader_check.py --build`生成清单；该命令会更改manifest，不能用它来证明已收到内容未变。

精确公开允许列表是[public_allowlist.txt](verification/public_allowlist.txt)，包含17项；manifest哈希其中其余16项，自身不做自引用。SHA-256是相对完整性检查，不是作者真实性签名。只发布该静态列表，无递归搜集；ZIP、cache、archives、第三方原文和父版本全部排除。

## 使用限制

此模块是小批量、条件于已编码输入的参考求交器；不是生产性能实现，不是已校准实机真值，也未集成回旧向量化前向核。zero-thickness共面语义、边界接触及open-segment约定必须明确保留。正确性证据只对应本目录最终代码哈希；用户输入的margin是否有效需另行验证。
