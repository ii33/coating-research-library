# SPARTA 输运验证 2026-10-05

真实官方 SPARTA 27 Aug 2026 已构建并执行，38 个有界方法案例通过本次检查。
这是合成方法验证，不是实机散射、双板/行星几何或真实材料预测。

先打开 `docs/transport_validation.html`：离线单文件，含公式、坐标图、曲线、全部限制与官方来源。

## 主要结果

- 有限方形源几何参考 0.2376441865；SPARTA 400k发射时为0.23743
- 12个几何案例的发射、接收、表面损失、出口与库存账差均为零
- 热表面源角/能量/方位分布单独验证；自然nrho通量发射实际99717，理论99713.8696
- 恒密度周期背景中读取每步真实碰撞历史，校验示踪ID唯一/守恒/集合成员与全局事件数
- 静止τ=.1五次均值0.90676；解析0.904837；热相对速度五次均值0.83272；解析0.831185
- 网格、时间步、权重均检查两个细化级；统计分辨率限制仍明确保留

## 复现

官方固定提交：e071055fca6ccd250d4b894dadb7ff64d6e6fcac。
`vendor/sparta/src/spa_serial` 为本目录内部编译，无全局安装。

```sh
make -C vendor/sparta/src -j2 serial
python3 scripts/study.py --stage all
python3 scripts/check_results.py
python3 scripts/build_report.py
```

## 证据入口

- `results/validation_summary.json`：冻结结果和状态
- `results/comparison.csv`：可排序的全部案例指标
- `results/*/input_contract.json`、`in.sparta`、`execution.json`：输入与真实执行
- `results/*/log.sparta`、`*.tally`、`pulse.dump`：原始读回
- `results/failed_attempts/`：上游tally/majorant/热浴反馈失败，不作成功结果
- `provenance/source_build.json`：版本、依赖、来源、命令与二进制hash
- `provenance/SPARTA_LICENSE.txt`：GPL v2许可

本研究仅写本目录；cub与本地工程不修改、没有提交或push。
