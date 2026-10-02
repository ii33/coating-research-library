# 第一轮独立证据抽查

日期：2026-10-02。范围：三本材料分册、手册总论、关键原始来源和数值例。性质是独立资料/工程抽查，不是用户指定完整模型审查链的替代，也不是实验验收。

## 结果

未发现阻断项或重大事实/算术错误。两项小问题已修正：

1. 氟化物/基片分册§0与总论§3.2补充“界面k可忽略的透明/弱吸收介质近似”，避免把简化平板界面公式用于强吸收材料
2. H4身份引用拆分：SUSONITY产品页OX-16支持La_xTi_yO_z类别；钛/镧氧化物形成稳定LaTiO3相的表述改引OX-17原厂PDF第1页。正文、来源登记和摘要同步修正

## 已直接核对的原始证据

- [Durante原文Table1/2](https://inspirehep.net/files/3c4e23b65057a6e6b3a6ea500307f62e)：名义零Ti样品确列EDS7.1±0.6%，作为非纯材料默认项隔离正确，未自行判断成因
- [H4原厂PDF](https://www.emdgroup.com/Products/PM/us/SUB_H4_H4HD_EMD_2022.pdf)：选录n/k、QCR密度与状态一致
- [Hellma ZnS表](https://www.hellma-materials.com/wp-content/uploads/2024/11/ZincSulfide_Cleartran.pdf)与[Crystran多光谱ZnS](https://www.crystran.com/optical-materials/zinc-sulphide-zinc-sulfide-multispectral-zns/)：硬度排序冲突是真实来源差异，不能平均
- [Ge CHARMS原稿](https://arxiv.org/pdf/physics/0606168)：温度/波长及所引n一致
- [McPeak原文](https://pubs.acs.org/doi/10.1021/ph5004237)：Cu/Al制备及模板剥离测面条件一致

全部16个金属派生谱点、Ge平板和ZnSe例做了独立重算，吻合。H4配方、K9实际牌号、本机膜密度/n/k及生产验证保持未知；未发现假装实测完成的声明。

## 范围限制

本抽查不是逐个原论文全文复审，也不验证每份SDS在用户所在地和实际供货批次的适用性。H4与K9身份缺口、本机校准和具体产品环境/损伤测试仍待开展。来源冲突保留，不因为抽查通过就转为设计默认值。

## 修订后闭环核对

两项小问题在分册、源登记、摘要和独立H4卡均已核实修正；聚合参数中OXP-011/OXP-012与IRP-007保持quarantined且design_ready=false。OXP-030、IRP-038、IRP-087和MP-062的严格上界保持“<”。修订后无新增问题；闭环核对没有宣称重新实施实验或完整模型审查。
