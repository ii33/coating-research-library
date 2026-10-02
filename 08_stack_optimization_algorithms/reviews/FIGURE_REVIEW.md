# 图像目视核查

四张SVG及对应PNG预览已逐张实际打开检查：标题/图例/坐标可读，无裁切或文本叠盖。

- 01_budget_accuracy：清楚标明墙钟单次观测、组合角度审计成本；不同方法成本不可只看训练值
- 02_holdout_spectra：展示留出中间AOI的s偏振，仅作示意，全角度/偏振仍以JSON为准
- 03_failures_and_robustness：欠采样峰、代理拒绝、经验CDF均保留合成非良率标签
- 04_gradients_and_constraints：差分误差U形趋势、7次核测时中位、厚度ε约束

图由自有代码和冻结计算数据生成，没有复用第三方插图。初次渲染fontconfig缓存警告未影响输出可读性；缓存目录已设为临时可写目录。
