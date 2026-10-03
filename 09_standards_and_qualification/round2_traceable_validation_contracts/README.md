# T09第二轮 可追溯验证与合格判定证据合同

版本 T09R2-1.0。研究日期 2026-10-02。结论：可运行的研究证据检查与原创验证合同已建立；真实计量、设备验证、产品鉴定及生产放行均未完成。数据检查通过不会输出生产合格声明。

本轮承接T08条件反演，把材料身份、读数语义、测量结果、设计预测、生产验收、环境及损伤鉴定分别建账。新增2026年BIPM非线性修订和Global ACI文件现行性核验，并将MXC手册中的失锁替代、参数切换、负厚舍弃、共享挡板旧源残余转为证据门槛。

## 阅读顺序

打开index.html可完全离线阅读全部报告，使用标题目录与全文搜索。报告原文件在reports；来源索引在sources/source_registry.json；结构schema、证据矩阵在contracts；tiny示例在examples。

1. 01范围与证据等级
2. 02标准版本与访问限制
3. 03溯源链与校准适用域
4. 04共享校准与相关性
5. 05拟合 选择 留出与变更
6. 06不确定度与决策规则
7. 07有限预算与不收敛
8. 08仪器语义与MXC案例
9. 09生产 环境 损伤资格
10. 10实现 验收 冻结与限制

## 最小运行

在此目录执行，建议设置PYTHONDONTWRITEBYTECODE=1。

reader已通过静态内容/链接/外部资源检查；视觉与交互浏览器验证未完成：dot云浏览器拒绝localhost，本地Chromium启动被环境socket权限阻止，授权重试仍失败。未声称桌面/手机截图验收通过。

    python models/evidence_contract.py --examples
    python -m unittest discover -s tests -v
    python models/freeze_package.py --verify

代码核心仅用Python标准库。独立JSON Schema检查可用现有jsonschema；这不是运行核心依赖。所有输入/结果都是synthetic_demo，程序拒绝输出生产放行。仅小型公式/字段反例执行；T08高算量driver仍not_run_awaiting_device，本轮不调用。

本轮只写此新增目录，不改T06/T07/T08及任何既有研究。完整指定模型审核链未运行；仅作者自查和一次窄单位/证据规则独立核查。无上传、推送、部署、外部分享、用户电脑操作或硬件测试。停止点是本地freeze。
