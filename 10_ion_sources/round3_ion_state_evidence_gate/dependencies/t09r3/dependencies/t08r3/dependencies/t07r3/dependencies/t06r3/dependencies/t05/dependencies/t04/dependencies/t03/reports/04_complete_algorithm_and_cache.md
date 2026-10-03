# 参考算法和缓存合同

## 一次完整有界局部步

以下步骤对应models/trust_region.py，不是只写提纲的伪代码。

```
输入冻结Scene、有限源(nodes,weights)、同一D*、panel预算、Δ、S
1 验证全部有限数、正板尺寸/高度层次、非负源率/权重、非零速度
2 读取输入不确定性；非零则unknown，停止候选排序
3 full_forward(p): 重建所有事件并计算闭式forward、光滑/事件Jacobian
4 用有理可见段Darboux积分给出D区间，再映射成J区间
5 r=(Dfloat−D*)/D*；j=(∂D/∂p)S/D*；g=rj
  event_aware用smooth+event；omit_events只用smooth
6 g=0则记录零模型梯度；pred=0拒绝ratio，不宣称真目标驻点
7 沿−g/||g||的Gauss-Newton Cauchy方向选长度
  ℓ=min(Δ, ||g||/(j·direction)²)，曲率零时ℓ=Δ
8 d=Sℓ direction；在所有有理仿射guards之前取0.8安全比例
9 编码新candidate；对实际端点整段重证所有guards，失败即拒绝
10 full_forward(candidate)，不得复用旧可见性或线性外推值
11 同一合同下以目标区间比较；unknown或重叠均unresolved
12 若pred下界<=1e−12拒绝；否则构造actual/pred区间
13 ρlo>=0.1且候选可证明改善才accept；否则reject或unresolved
14 只输出下一Δ建议；下一迭代必须从第1步重建
```

当前只执行一次event_aware和一次omit_events，不循环到人为“通过”。Δ失败/未决时建议减半，成功且ρlo>0.75时建议至多扩大到2；不自动执行建议。没有BFGS历史、长期线搜索或大范围多起点搜索。

## 单元边界和复杂度

event_reference.py、analytic_oracle.py与两个底层冻结依赖是字节不变的T02输入。新增trust_region.py只从包内导入它们。rational_forward_interval独立于闭式原函数验证值，analytic_oracle以另一种表达式核对一阶梯度，但两者仍共享同一物理假设。

n个有限节点、每段N面板最多2nN个有理面板，事件排序O(n log n)，节点上各有两面两边候选。Fraction的分子/分母位数随精确加法增长，不能把面板计数直接等同CPU耗时；这是小型正确性参考，不是GPU内核。完整生产扩展需要区间库、稳健事件求解和已验证误差模型。

## 完备缓存键

每个评价的cache_key是canonical JSON的SHA-256，绑定：

- Scene所有字段：源/靶横移、运动起点/速度/时钟、H、板b/a/near/far/y半宽、过程t0/t1、A/q0/q1、数值guards及几何未知半径
- 固定的三维源/靶/板坐标架、法向、旋转、y/z位置与有限闭板语义；可配置部分在Scene中，固定部分仍显式写入合同
- 全部源节点及权重、参考源率时钟语义
- 参数单位、目标表达式和D*、归一化分母阈值
- 有理包络方法、面板数、光滑导数求积阶数、输入不确定性资格
- 模型版本及models下所有Python文件内容hash，含冻结依赖
- 当前活动面事件身份及评价资格状态

cache不是以direction、板ID、单个Jacobian或某次运行标签为键。方向只影响提议，不决定forward。common_contract签名排除设计b/a，允许比较两个新板形；除此之外全部绑定。cache_key再加入b/a与事件身份。当前参考实现产生并测试这些键，不实现磁盘共享缓存或跨机缓存服务。

当板厚、源时钟、源节点权重、单位或代码变化，键必须变化。单元测试逐项扰动关键字段并确认；读者manifest与冻结依赖hash提供文件层的另一条链。hash证明内容身份，不证明内容正确。

## 设备driver与配置

models/device_driver.py默认仅加载data/device_validation_plan.json、验证严格schema并打印预算，不运行验证。配置冻结输入hash，允许在新配置中变面板数、局部Δ、两轴尺度、D*及预算；几何/源本体仍从包内冻结合同读入。两种方法成对必跑，避免只保留有利方法。

当前计划为面板64/128/256、半径0.25/0.5/1、最多18个trial调用、10752个有理面板的保守上界，单进程，墙钟120秒。额度是研究上限，不是速度承诺。授权恢复后，应先在指定设备验证配额、权限与环境，再复制plan到新运行目录，写入真实授权证据标识和设备标签；本包的False/plan_only不能原地修改。

运行入口同时要求--run、execution_authorized=true、execution_mode=explicit_authorized_run、授权证据、设备标签及全新包外输出目录。当前默认--run应退出2。声明字段不是用户权限的替代物，操作者仍须得到当前有效授权。本轮没有启动该入口，也没有任何远程控制代码。

每个完整trial之后写checkpoint，CANCEL文件和墙钟在trial边界检查。单个有界trial可能越过墙钟，故不声称硬实时截止。发生未知几何/重叠时按预注册规则停为partial；不静默改面板或改目标。输出保存输入/代码hash、完成单元数与原始结果；不自动上传、不覆盖冻结证据。
