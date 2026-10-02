# 光学镀膜相关 MIL 与 GB/T 标准公开目录核验

查询日期：2026-10-02。用途：通用工业光学镀膜质量研究。本文只核验公开目录、状态、日期、采标关系及必要的公开通知，不构成完整标准条文的符合性审查；没有给出武器系统设计、适配或验收方案。

结构化数据：[official_status_mil_gb.json](../../data/official_status_mil_gb.json)，共 27 条标准行。每行含官方URL、证据短摘录、摘要、可得性和限制。

## 先用这六条结论

1. **MIL-PRF-13830B真实存在且DLA目录仍为Active。** B修订基础日期为1997-01-09，最近是2023-02-24的Notice 5（Validation）。不要写成“13830B:2023新版”，也不要忽略通知。目录未列B以后的修订字母。
2. **MIL-C-14806A、MIL-C-675C、MIL-C-48497A均检索到Inactive状态，不能统一标“现行”或“已取消”。** 这里的Inactive是Inactive for New Design；后来的Validation不等于Reactivation。未核实它们被某个ISO标准正式替代。
3. **MIL-STD-810的目录最新组合是H + Change 1（2022-05-18），状态Active。** H原版日期2019-01-31。官方目录Scope要求按实际环境/性能需求作裁剪，不直接施加设计或试验规格；它本身不是所有镀膜的统一验收门槛。
4. **GB/T 26332.4-2026已于2026-06-01实施，2015版同日废止。** GB/T 26332.1-2024也已现行。不能用旧2015/2018表单概括全系列。
5. **GB/T 26332.2-2026、.3-2026于2026-09-28发布，但2027-01-01才实施。** 截至查询日，2015版仍现行，2026版状态为“即将实施”。这不是两个版本都已实施。
6. **GB采标年份和一致性必须逐项保存。** 26332.1-2024以及.4-2026、.5～.8-2022是MOD；.2/.3-2015是IDT；即将实施的.2/.3-2026转为MOD。GB/T 16601.1～.4-2017均为MOD，采用的是2011年的ISO/ISO TR文件，不意味着采用当前最新ISO版本。

## A. MIL公开目录

DLA的[QuickSearch帮助](https://quicksearch.dla.mil/qsHelp.aspx)将Active、Inactive for New Design和Canceled区分为不同文档状态。Inactive用于支持/再采购既有项目的范围，不能当作新设计通用依据；Canceled另有取消通知。Document Date可能是最近notice/change/amendment日期，不等于基础修订日期。目录中“Next Review Due”到期也不能自行解释成取消。

| 编号及修订组合 | 基础修订日期 | 最近目录动作 | 目录状态 | 官方来源 |
|---|---|---|---|---|
| MIL-PRF-13830B | 1997-01-09 | Notice 5 — Validation，2023-02-24 | Active | [DLA目录](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=10290) |
| MIL-C-14806A | 1969-06-12 | Notice 3 — Validation，2013-10-29 | Inactive for New Design | [DLA目录](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=10834) |
| MIL-C-675C | 1980-08-22 | Notice 3 — Inactivation，2014-05-06 | Inactive for New Design | [DLA目录](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=2500) |
| MIL-C-48497A | 1980-09-08 | Notice 2 — Validation，2013-10-29 | Inactive for New Design | [DLA目录](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=26444) |
| MIL-STD-810H w/Change 1 | 2019-01-31 | Change 1（已并入），2022-05-18 | Active | [DLA目录](https://quicksearch.dla.mil/qsDocDetails.aspx?ident_number=35978) |

### 逐项题名、可得性和证据

#### MIL-PRF-13830B

- 题名：Optical Components for Fire Control Instruments; General Specification Governing the Manufacture, Assembly, and Inspection of
- 官方短证据：Status: Active
- 摘要：目录修订史的最近修订字母为B，基础修订日期1997-01-09；2023-02-24是验证通知日期，不是B版重新发布或新修订。目录未显示B以后的字母修订。
- 通知链：Notice 2 — Reactivation（2000-01-07）；Notice 3 — Validation（2013-03-14）；Notice 4 — Validation（2018-01-12）；Notice 5 — Validation（2023-02-24）
- 使用界限：仅作公开目录核验。标准标题及范围具有原有军事背景；此处不提供武器系统设计、适配或验收方案。

#### MIL-C-14806A

- 题名：Coating, Reflection Reducing, for Instrument Cover Glasses and Lighting Wedges
- 官方短证据：Status: Inactive
- 摘要：官方目录保留Inactive状态；2013年验证通知没有使其重新成为Active。验证通知说明仍不用于新设计，但文档可在其允许范围内使用。
- 最新目录amendment：2，1974-05-01
- 通知链：Notice 2 — Inactivation（1997-03-14）；Notice 3 — Validation（2013-10-29）
- 替代关系：目录未列出正式替代文件；未核实为Canceled，不可推定ISO 9211正式取代该MIL文件。
- 通知来源：[1. DLA官方公开验证通知的索引内容](https://quicksearch.dla.mil/Transient/219B7875875E4EF29C25908D3DC4AE5D.pdf)

#### MIL-C-675C

- 题名：Coating of Glass Optical Elements (Anti-Reflection)
- 官方短证据：Status: Inactive
- 摘要：官方目录索引显示Inactive；2014年Notice 3明确限制新设计用途，仅保留替换用途。未发现正式取消或替代目录项。
- 最新目录amendment：3，1986-08-20
- 通知链：Notice 2 — Reinstatement（1996-10-10）；Notice 3 — Inactivation（2014-05-06）
- 可得性限制：目录直接打开失败，以上目录证据来自官方URL的搜索索引，页面自报更新2025-06-16，较查询日旧。2014年正式通知可交叉印证，但不能把旧缓存冒充当日在线实时核验。
- 冲突：目录将Amendment 3日期列为1986-08-20，Notice 3正文却把1996-10-10与Amendment 3关联；1996-10-10在目录中对应Notice 2 Reinstatement。保留此不一致，引用时分开列基础版、amendment及notice，不擅自修正原件。
- 通知来源：[1. DLA官方公开Inactivation通知索引](https://quicksearch.dla.mil/WMX/Default.aspx?token=5730239)；[2. DLA官方公开Inactivation通知索引](https://quicksearch.dla.mil/Transient/D2D54CA414CB46129B7BC2783B9FAD90.pdf)

#### MIL-C-48497A

- 题名：Coating, Single or Multilayer, Interference: Durability Requirements for
- 官方短证据：Status: Inactive
- 摘要：官方目录显示Inactive；2013年验证通知保持不用于新设计的状态。目录范围描述单层/多层干涉膜的耐久性，主要置于密封光学系统保护环境内；不能由标题泛化为所有外露光学镀膜的通用验收标准。
- 最新目录amendment：3，1995-02-21
- 通知链：Notice 1 — Inactivation（1997-03-14）；Notice 2 — Validation（2013-10-29）
- 替代关系：目录未列出正式替代文件；未核实为Canceled。
- 通知来源：[1. DLA官方公开验证通知索引](https://quicksearch.dla.mil/WMX/Default.aspx?token=5726288)

#### MIL-STD-810H w/Change 1

- 题名：Environmental Engineering Considerations and Laboratory Tests
- 官方短证据：Status: Active
- 摘要：目录最近为H版Change 1（修改已并入）；2022-05-18是Change 1日期，H版原日期2019-01-31。
- 使用界限：官方范围说明该文档不直接规定设计或试验规格，而指导依具体性能需求作环境裁剪。因此它不是光学镀膜的统一合格阈值，也不能凭通过某一方法声称获得通用MIL-STD-810认证。

MIL文档在所读目录修订历史中列为Distribution Statement A，公开目录及部分通知可读。本次**未核完整规范正文、未执行逐条款审查、未提取试验严酷度和合格限值**。13830B与810H的Scope结论来自正式目录范围栏，不伪装成正文具体条款引用。MIL-C-675的直接详情页访问失败，使用的官方搜索索引自报数据更新时间为2025-06-16，因此该行状态应在正式签约前再次在线复核；公开2014年Notice 3与该Inactive结论一致。DLA的Transient和WMX链接可能变动，持久检索入口为每行的Document Details页。

## B. GB/T 26332光学薄膜系列

IDT＝等同采用；MOD＝修改采用。采标关系取正式国家标准条目，不能由名称相近、分册号相同或项目立项页面推断。

| 国家标准 | 标题分部（共同前缀：光学和光子学 光学薄膜） | 发布 / 实施 | 查询日状态 | 采用标准及一致性 |
|---|---|---|---|---|
| [GB/T 26332.1-2024](https://std.samr.gov.cn/gb/search/gbDetailed?id=234D7936AAA0E194E06397BE0A0AA0A9) | 第1部分：术语 | 2024-09-29 / 2025-04-01 | 现行 | ISO 9211-1:2024，MOD |
| [GB/T 26332.2-2015](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D80FF3D3A7E05397BE0A0AB82A) | 第2部分：光学特性 | 2015-12-10 / 2016-07-01 | 现行 | ISO 9211-2:2010，IDT |
| [GB/T 26332.2-2026](https://std.samr.gov.cn/gb/search/gbDetailed?id=5CB12E0EFBED2034E06397BE0A0A34FB) | 第2部分：光学特性 | 2026-09-28 / 2027-01-01 | 即将实施 | ISO 9211-2:2024，MOD |
| [GB/T 26332.3-2015](https://std.samr.gov.cn/gb/search/gbDetailed?id=NFSYBqcNMTs%3D&mode=p) | 第3部分：环境适应性 | 2015-12-10 / 2016-07-01 | 现行 | ISO 9211-3:2008，IDT |
| [GB/T 26332.3-2026](https://std.samr.gov.cn/gb/search/gbDetailed?id=5CB12E0EFB382034E06397BE0A0A34FB) | 第3部分：环境适应性 | 2026-09-28 / 2027-01-01 | 即将实施 | ISO 9211-3:2024，MOD |
| [GB/T 26332.4-2026](https://std.samr.gov.cn/gb/search/gbDetailed?id=4C1BF798CB2F83B0E06397BE0A0A640A) | 第4部分：摩擦、附着力和耐水性的试验方法 | 2026-02-27 / 2026-06-01 | 现行 | ISO 9211-4:2022，MOD |
| [GB/T 26332.4-2015](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D80F97D3A7E05397BE0A0AB82A) | 第4部分：规定的试验方法 | 2015-12-10 / 2016-07-01 | 废止 | ISO 9211-4:2012，IDT |
| [GB/T 26332.5-2022](https://std.samr.gov.cn/gb/search/gbDetailed?id=EB58F4DA9266B2A2E05397BE0A0A7D33) | 第5部分：减反射膜基本要求 | 2022-10-14 / 2023-05-01 | 现行 | ISO 9211-5:2018，MOD |
| [GB/T 26332.6-2022](https://std.samr.gov.cn/gb/search/gbDetailed?id=EB58F4DA9152B2A2E05397BE0A0A7D33) | 第6部分：反射膜基本要求 | 2022-10-14 / 2023-05-01 | 现行 | ISO 9211-6:2018，MOD |
| [GB/T 26332.7-2022](https://std.samr.gov.cn/gb/search/gbDetailed?id=EB58F4DA9158B2A2E05397BE0A0A7D33) | 第7部分：中性分束膜基本要求 | 2022-10-14 / 2023-05-01 | 现行 | ISO 9211-7:2021，MOD |
| [GB/T 26332.8-2022](https://std.samr.gov.cn/gb/search/gbDetailed?id=SQJXNm6kWeg%3D&mode=p) | 第8部分：激光光学薄膜基本要求 | 2022-10-14 / 2023-05-01 | 现行 | ISO 9211-8:2018，MOD |

### 替代、过渡和来源冲突

- [26332.1-2024正式标准条目](https://std.samr.gov.cn/gb/search/gbDetailed?id=234D7936AAA0E194E06397BE0A0AA0A9)列出全部代替26332.1-2018，采ISO 9211-1:2024（MOD）；[早期项目页面](https://std.samr.gov.cn/gb/search/gbDetailed?id=C84EE653070A4B14E05397BE0A0AC1BD)还写ISO 9211-1:2018。采用正式发布条目，不把历史立项目标当成最终采标年份。
- [26332.4-2015条目](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D80F97D3A7E05397BE0A0AB82A)列2026-06-01废止，且全部由26332.4-2026代替；[2026版公开题录](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=246748404692E914C88FA400E924F2B0)与状态及日期一致。正式CNF视图载明MOD采用ISO 9211-4:2022，不能沿用旧版的IDT/2012。
- [.2-2026](https://std.samr.gov.cn/gb/search/gbDetailed?id=5CB12E0EFBED2034E06397BE0A0A34FB)与[.3-2026](https://std.samr.gov.cn/gb/search/gbDetailed?id=5CB12E0EFB382034E06397BE0A0A34FB)的正式条目在官方搜索索引中显示“即将实施”，2027-01-01分别全部替代2015版。直接打开返回缓存未命中；这是取得方式的限制，不应删除已发现的新版本，也不能把索引当成实时后台查询。旧标准页的修订计划字段可能仍显示“正在批准”，应与新发布条目分开处理。
- **26332.5～.8-2022发布日期存在官方平台冲突：** std.samr正式条目均列2022-10-12；openstd题录及[官方公开通知](https://openstd.samr.gov.cn/bzgk/std/nd?no=1841)列2022-10-14。本表优先使用公开通知/题录的10-14，同时JSON保存10-12备选值及冲突说明；不声称主管部门已纠正差异。两平台实施日期均为2023-05-01，现行状态和编号一致。
- 26332.8的早期项目曾记“等同采用”，但[正式标准条目](https://std.samr.gov.cn/gb/search/gbDetailed?id=SQJXNm6kWeg%3D&mode=p)是MOD采用ISO 9211-8:2018，应以后者为准。
- 本系列采用ISO标准。openstd题录明确提示因采标版权不提供文本阅读服务；本次仅保存题录与原创摘要，不获取受限全文。目录采标关系不能替代逐条差异核对，也不说明GB和最新ISO技术内容完全一致。

## C. 激光损伤阈值：中国国家标准与ISO 21254的关系

| 国家标准 | 完整题名 | 发布 / 实施 | 状态 | 采用标准 |
|---|---|---|---|---|
| [GB/T 16601.1-2017](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D828C1D3A7E05397BE0A0AB82A) | 激光器和激光相关设备 激光损伤阈值测试方法 第1部分：定义和总则 | 2017-12-29 / 2018-07-01 | 现行 | ISO 21254-1:2011，MOD |
| [GB/T 16601.2-2017](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D82631D3A7E05397BE0A0AB82A) | 激光器和激光相关设备 激光损伤阈值测试方法 第2部分：阈值确定 | 2017-12-29 / 2018-07-01 | 现行 | ISO 21254-2:2011，MOD |
| [GB/T 16601.3-2017](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D82394D3A7E05397BE0A0AB82A) | 激光器和激光相关设备 激光损伤阈值测试方法 第3部分：激光功率（能量）承受能力确信 | 2017-12-29 / 2018-07-01 | 现行 | ISO 21254-3:2011，MOD |
| [GB/T 16601.4-2017](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D828C0D3A7E05397BE0A0AB82A) | 激光器和激光相关设备 激光损伤阈值测试方法 第4部分：检查、探测和测量 | 2017-12-29 / 2018-07-01 | 现行 | ISO/TR 21254-4:2011，MOD |

四个正式条目均标“现行”，且均为**修改采用**；不能写成GB/T 16601“等同ISO 21254全系列”。第4部分采用的是ISO/TR 21254-4:2011，保留TR标记。第3部分正式题名使用“确信”，同页采标中文名称出现“确认”，表格按正式标准题名保留“确信”。这里只核对应关系，不核LIDT完整试验程序或提供阈值设计建议。ISO自身的更新应另查ISO官方目录，尤其不能把GB采用的2011年份误认为ISO当前年份。

## D. GB/T 2423环境试验方法

这些是通用环境试验方法，不等于光学镀膜验收规范。采用某方法仍需确定适用试样、环境条件、试验顺序、试验前后光学测量以及合同/产品标准的合格判据。不会从方法标题臆造所有镀膜都适用的时间、温度、循环次数或允许性能变化。

| 标准 | 完整题名 | 发布 / 实施 | 状态 | 采用IEC及一致性 |
|---|---|---|---|---|
| [GB/T 2423.1-2008](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7C61BD3A7E05397BE0A0AB82A) | 电工电子产品环境试验 第2部分：试验方法 试验A：低温 | 2008-12-30 / 2009-10-01 | 现行 | IEC 60068-2-1:2007，IDT |
| [GB/T 2423.2-2008](https://std.samr.gov.cn/gb/search/gbDetailed?id=ECxi9pU8n8Y%3D&mode=p) | 电工电子产品环境试验 第2部分：试验方法 试验B：高温 | 2008-12-30 / 2009-10-01 | 现行 | IEC 60068-2-2:2007，IDT |
| [GB/T 2423.3-2016](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D81601D3A7E05397BE0A0AB82A) | 环境试验 第2部分：试验方法 试验Cab：恒定湿热试验 | 2016-12-13 / 2017-07-01 | 现行 | IEC 60068-2-78:2012，IDT |
| [GB/T 2423.4-2008](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D76D77D3A7E05397BE0A0AB82A) | 电工电子产品环境试验 第2部分：试验方法 试验Db：交变湿热（12h＋12h循环） | 2008-05-19 / 2009-01-01 | 现行 | IEC 60068-2-30:2005，IDT |
| [GB/T 2423.17-2024](https://std.samr.gov.cn/gb/search/gbDetailed?id=208E903AB60D79F3E06397BE0A0AB2B9) | 环境试验 第2部分：试验方法 试验Ka：盐雾 | 2024-08-23 / 2025-03-01 | 现行 | IEC 60068-2-11:2021，IDT |
| [GB/T 2423.18-2021](https://std.samr.gov.cn/gb/search/gbDetailed?id=4AnpE9dVlt0%3D&mode=p) | 环境试验 第2部分：试验方法 试验Kb：盐雾，交变（氯化钠溶液） | 2021-05-21 / 2021-12-01 | 现行 | IEC 60068-2-52:2017，IDT |
| [GB/T 2423.22-2012](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7E67ED3A7E05397BE0A0AB82A) | 环境试验 第2部分：试验方法 试验N：温度变化 | 2012-12-31 / 2013-06-01 | 现行 | IEC 60068-2-14:2009，IDT |

- 盐雾Ka使用2423.17-2024，已全部代替2423.17-2008；交变盐雾Kb使用2423.18-2021，已全部代替2423.18-2012。两者的方法含义与对应IEC年份不同，不能只写“盐雾按GB/T 2423”。
- 低温/高温的.1/.2-2008目录仍列现行，已有修订计划不等于新标准已发布。温度变化.22-2012目录同样现行；其20253281-T-469计划显示正在批准，不能编一个已生效新版本。
- 恒定湿热Cab与交变湿热Db分列，不能在质量计划中互换。本文不对新出现的其他组合环境试验分册作穷尽整理。

## E. GJB核验缺口

在gov.cn、mil.cn、std.samr.gov.cn公开索引做了光学薄膜/镀膜相关GJB标准目录检索，未找到足以确认具体编号、标题、版本和当前状态的公开官方权威记录。因此本次结论为**未能核实**，不猜编号，不以商业下载站或其他二手列表拼出“现行国军标清单”；也不据此断言不存在相关标准。若合同明确给出GJB编号，应由拥有合法权限的责任方提供授权文本及适用版本，再进行边界内核对。

## 证据等级与引用规则

- 正式目录中的状态、版本日期和采标记录是本文依据；只读索引/缓存的条目明确披露。查询日期不是源站数据更新时间。
- “现行/Active”是目录状态，不等于可不加条件地适用于任意产品；目录存在也不代表完成了资质、产品合格或实验室能力认可。
- 验证通知、技术修订、amendment、change和实施日期分别记录。不要把保留有效、重新启用和取消混为一谈。
- 严格采用受控的具体版次引用；拟改用新版本、国际版本或另一国家采用版本时，应记录差异评审，而非仅把编号字符串替换。
- 没有复制、购买或保存标准正文。JSON中的“全文可得性”仅描述官方公开题录/版权提示，本次实际获得的是元数据及少数公开通知摘要。

