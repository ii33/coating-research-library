# PO-S06 · NIST参考积分球的方向-半球反射量

- 官方页面：[Reference Integrating Sphere for Spectral Reflectance](https://www.nist.gov/laboratories/tools-instruments/reference-integrating-sphere-spectral-reflectance)
- 本次核验：2026-10-02，重读NIST仪器说明与规格表。

NIST称该参考系统针对室温、光谱中性、非荧光样品做方向-半球反射测量，使用经校准的压制PTFE标准。页面给出的关键条件是8°照明、镜面分量包含、半球观察；光谱范围250–2400 nm、14 nm带宽、线偏振或非偏振，报告反射因子。网页列出的k=2最小相对不确定度为0.4%，并明确实际值随样品而变。

这提供了模型与验收之间的一个重要接口：平面相干TMM算出的理想镜面R不等于自动包含散射的方向-半球反射因子。若要把散射作为残差，需要再有specular-excluded测量或BRDF/角分辨数据；此页面的“specular included”测量不能单独分离镜面反射与散射。

## 适用边界

以上数值是NIST参考仪器的页面能力，不是用户本机测量、校准状态或任意样品的不确定度。最小样品尺寸45 mm和10 mm采样口径等条件也限制适用样品；非荧光、光谱中性条件不可忽略。

## 权利与档案

仅登记NIST公开仪器页面并保存原创摘要，不抓取图片或整页副本。
