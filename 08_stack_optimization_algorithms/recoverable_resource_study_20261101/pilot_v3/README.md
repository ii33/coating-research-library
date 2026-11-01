# 新可恢复参考数据试验：12 项先导任务（v3）

这是独立新试验，不重建或冒用缺失的旧 64 组数据；不训练或验收广义预测模型，也不使用实际四窗口工程目标。v3 从未运行的 v2 协议源码建立，不复用 v2 的 plan、案例或输出；只加固准入和恢复契约，不改变搜索、种子、目标、评价和预算。

- 两个新合成材料组（41000、41001）× 六类目标。全部 n/k、基片、目标窗口、平均/逐点、严格性、角度和偏振保存在 12 个 `cases/*/input.json`。合成曲线不是实测工艺数据；组间须隔离，不能用于泛化评估。
- 固定发布核心 `131d3fc989c3dc9ac8d94fee3c39541a61b851df`，单前面、空气入射、半无限基片；未指定工艺层厚限制。核心的受跟踪源码必须干净且 HEAD 匹配。
- 参考流程：0/2/4/8/12/16/24/32 初始层数；周期、匹配/啁啾、固定种子随机序列共三起点；41 点局部残差/解析梯度修复，最多 60 次函数评价；45 秒为协作式数值预算，不是整案例硬墙钟 SLA（单次调用、输入准备和落盘不被异步抢占）。最多两个通过层数档后进入两轮减层，每轮最多两项提案。厚度区间为参考波长的 1e-7 至 2 倍，均为数值努力限制，非物理下界或制造要求。
- 独立数值审计使用原请求和核心的 32 倍网格，已知 k 不清零。通过审计的同一设计给出成对 N、D；无见证保持未知。通过审计立即在本机原子持久化完整候选和审计后才继续搜索。
- 选点采用 `log(1+N)+log(1+D/λ_ref)`，同分依次按 N、D、物理设计哈希。参考波长是各窗口几何中心的几何平均，层数与厚度不拼接。搜索是有限预算参考，不证明最小值或不可行。
- 工作集准入显式 256 MiB、CPU 工作线程和批量量子均为 1。BLAS 的实际运行库和线程独立记录并核对，详见下文。

## 冻结、准入和恢复

先在干净目录准备，然后将完整源码、文档、plan、source manifest 和全部输入发布至研究库，并由操作者复读核验，再运行第一小批。`source_manifest.json` 冻结源码、文档、plan 和 12 个输入的路径、长度和 SHA-256；它不包含自身，后续结果不修改它。源码改动必须使用新协议目录。每批将所有完整见证和结果同步并复读核验后再进行下一批；本机即时落盘不是远端备份。

示例（提前安装与 plan 记录相同版本的 Python、NumPy、SciPy 和 threadpoolctl）：

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export COATING_CORE_REPOSITORY=/path/to/coating-sim
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_reference_contract test_pilot_admission
PYTHONDONTWRITEBYTECODE=1 python run_pilot.py --repo "$COATING_CORE_REPOSITORY" prepare
# 将全部源码、plan、source_manifest 和输入发布并远端复读；独立记录 commit 和两项摘要。
PYTHONDONTWRITEBYTECODE=1 python run_pilot.py --repo "$COATING_CORE_REPOSITORY" run \
  --case train-41000-ar --verified-checkpoint <40位commit> \
  --verified-plan-sha256 <远端复读plan的64位SHA256> \
  --verified-source-manifest-sha256 <远端复读source_manifest的64位SHA256>
```

三个参数是操作者外部核验的记录，不是凭据。程序对本地 plan 和 source manifest 原始字节作摘要核对，并核对源清单、计划列出的源码与全部输入；只允许声明案例输出、批次和缓存等后续文件。**程序不联网，不能自行证明操作者提供的 commit 与两摘要确实关联或已被远端复读**。批次输出由操作者另行发布、复读与核对，不属于不可变源清单。

plan 不含私人路径，记录 Python、NumPy、SciPy、threadpoolctl、操作系统、架构、运行 BLAS 版本/线程和常见线程环境变量。准入要求这些值相符；不匹配应建立新协议或恢复原环境，不得静默降级。同硬件、相同软件和 45 秒预算也不能保证逐次优化轨迹或 bitwise 输出相同，因为时钟调度与数值实现可影响有限时间搜索。

完成结果重读前逐一核验全部列出见证的文件名、请求/设计哈希及审计与设计资源对应，重算选点并检查标签；无见证必须是 unknown、N/D 和选中哈希均为 null。尚未完成但有已保存见证的任务可重启有限搜索并保留它们；不声称可逐迭代恢复优化器状态或相同剩余时间。目录、结果或见证不一致即停止，不覆盖原文件。

2 组先导不足以度量预测泛化，不给出精度或区间覆盖宣称；既有 3 层、正厚度 MAPE 25% 的研究门槛不改变。[算法及数值边界](docs/algorithms.html)。
