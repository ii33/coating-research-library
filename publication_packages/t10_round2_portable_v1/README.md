# T10 Round 2 portable research reader v1

独立派生可携包，2026-10-02。仅供原创研究阅读、包内完整性检查和轻量合成复算；不是原冻结ZIP，也不继承原全项目审计通过状态。

## 阅读与身份

离线打开 [index.html](index.html)。八章物理/数学正文、三张原PNG及其SVG、数值内核、数据合同、例子和33项小测试均保留源字节。原章8和原交接中的冻结/审计叙述属于历史源包；当前命令和身份以本文为准。

- [独立派生清单](derived_manifest.json)覆盖当前载荷的准确路径、大小、SHA256
- [派生收据](derived_receipt.json)记录本包清单身份和新执行结果
- [完整来源映射](DERIVATION_MAP.json)逐项列出源路径/哈希、派生路径/哈希、变更或排除原因
- [准确发布允许清单](PUBLICATION_ALLOWLIST.txt)是唯一候选文件集，包括自身、清单和收据；不表示已获发布许可
- [历史审计边界](history/README.md)区分原全项目审计与新包内检查
- [MXC书目溯源](dependencies/manual_studies/2026-10-02_morningtech_mxc/evidence/provenance.json)及[页码证据](dependencies/manual_studies/2026-10-02_morningtech_mxc/evidence/page_evidence.csv)不含私有存储身份

原freeze_manifest.json身份为 de60f6e1e24e3a2d69b11e0cf3363e221b759e520e3e479e1e8b974bc5bae74b，仅标识源包；派生包使用新清单与新收据。源ZIP未复制，源文件未修改。不存在第三方原文、手册截图/完整厂商表、缓存或凭据。公开书目/官方来源链接保留；离线运行不请求网络。

## 支持的包内命令

在此目录运行。完整性检查只需 Python 3.10+ 标准库，不读取上游、兄弟目录、原ZIP或项目快照：

    python -B models/verify_portable.py --verify

数值复算另需 requirements.txt 中的 NumPy、SciPy、jsonschema；第三方软件本身不随包分发。新验证的实际版本见 verification/derived_validation.json，不把已安装环境等同于随包提供运行时。本次未安装软件。

    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B models/validation_driver.py
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B models/validation_driver.py --mode tiny_synthetic
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B models/validation_driver.py --mode offline_packet --input examples/synthetic_complete.json
    PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B models/validation_driver.py --mode offline_packet --input examples/actual_unknown.json

默认入口只输出未执行计划。最后两条只验证随包的合成/缺项样例，后一条应返回 blocked_evidence；不是实际设备记录验收。命令只写标准输出；若保存新结果，将其放到包外的新路径，勿覆盖冻结载荷。源driver中的重合成分支保留原字节，但不是本包轻量验证步骤，未执行。

## 准确边界

[新验证记录](verification/derived_validation.json)与新派生收据只证明：允许清单/字节完整性、所有活动HTML/Markdown本地链接、离线入口和33项小测试在隔离临时副本中通过；无上游文件依赖。链接检查是静态结构检查，不是浏览器渲染验收，也不核对外部网页是否仍在线。输入身份哈希不认证作者、来源真伪或安全签名。

浏览器布局未验证，既有权限拒绝路线没有再尝试。历史三张PNG视觉检查没有在本次重做。未运行完整43200逆解、实测数据、实时硬件、材料响应或生产/环境/损伤资格验证；未执行新的正式或独立审查。T02 partial、T03净侵蚀不支持、点12 not_run、τ非严格及其余上游限制全部保留。

背景依赖中的23个旧链接得到导航层处理：已有来源ID指向原登记公开书目URL；未附的材料卡/旧审查作为明确的非导航上游引用保留，详见 DERIVATION_MAP.json。这些不是支持命令的运行依赖。未伪造缺失文件或新增来源访问级别。

原审计依赖原ZIP、外置收据、21个上游文件及全项目快照，不能在本包运行并宣称通过。源审计历史复制仅供追溯。派生清单不哈希自身或收据以避免循环；收据单向绑定清单，清单覆盖允许清单及验证证据。这是完整性账本，不是数字签名。所有新增生成文件的来源类别与循环排除原因有明示。

本包仅本地准备；没有上传、push、GitHub、Library、部署、外部分享或用户电脑操作。发布由协调者另行决定。
