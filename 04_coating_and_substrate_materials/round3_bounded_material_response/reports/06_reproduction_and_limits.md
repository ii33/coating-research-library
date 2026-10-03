# 6 独立复算、冻结与剩余限制

## 6.1 包的组成

models/bounded_response.py是本轮响应参考核；models/run_examples.py为小型反例；models/device_driver.py是完整有界精化入口，默认只列计划。dependencies/t03保留完整forward实际依赖的原始字节副本，data/frozen_dependencies.json逐项绑定原项目路径、复制路径、字节数和SHA256。为保持上游code_hashes集合一致，T03全部models字节均复制；其中旧device_driver仅为冻结来源，不是本轮执行入口，不应运行。dependencies/context为原需求/前轮合同的只读快照，属于历史上下文，内文跨专题链接不作为运行依赖。

独立reader包含所有计算所需代码/输入和原创报告、图、来源摘要。它不会从兄弟T02/T03目录动态导入，不依赖当前项目根目录，读取本包的vendored依赖即可。来源原文、原文文本转换件、local快照清单、zip和外部release receipt均排除reader内容清单。

## 6.2 复算步骤

解压reader到任意新目录；先运行python -B verification/reader_check.py，校核完整内容manifest及23项复制依赖；再运行python -B -m unittest discover -s tests -v。最后运行python -B models/device_driver.py确认默认plan_only。

如要重算小例子，运行python -B models/run_examples.py --output /某个新输出位置/tiny_results.json。只在有numpy的环境执行；schema测试另需jsonschema。包不自动安装软件、联网或访问设备。读取reader.html无需服务端，所有图为本地相对资源。HTML布局未做真实浏览器渲染检查，不能以文件结构检查代替像素排版检查。

本次独立解压验证会记录：manifest校核、30项小测试、plan_only、重算关键数值与冻结结果的一致性。不重新执行独立单位审核，避免把同一窄审核重复运行称多轮复核。

## 6.3 冻结身份

verification/reader_manifest.json精确枚举每个reader payload文件的路径、字节和SHA256；不自包含。zip另外含这个manifest本身。verification/release_receipt.json放在zip外，记录zip字节数/条目数/hash、manifest hash及payload聚合hash，无自引用循环。verification/freeze_record.json保存本地冻结状态，不等价于物理认证。

为了防止“清单通过”被误解成科学结论，reader_check只称integrity_passed。科学范围由六章正文、小算例、测试与窄独立检查共同界定；没有正式指定模型链签署。

## 6.4 本轮修复记录

自测曾发现schema测试直接把Python tuple交给JSON Schema验证器，产生1项测试错误。已修正测试入口为实际JSON序列化后的数组，重跑30项全通过；没有放宽数值域或掩盖null。driver检查点在每个forward完成后写出，确保调用间取消能保留已完成输入的结果。

## 6.5 不能由本包支持的结论

- 不给真实SiO2、ZnS、YbF3、H4通用s、密度、应力或附着数值
- 不从源电压生成到靶E，不从QCM显示厚度生成独立膜密度
- 不从条件材料盒生成置信概率/批次良率
- 不认证连续源、任意CAD、任意运动/事件拓扑或非仿射历史
- 不称T02 point12/point2缺口已完成，不删去上游事件项
- 不把两个局部板候选称全局最优或整片均匀性优化
- 不改变本机授权、hostquota或远控路由，不运行待授权重driver
- 不给制造放行、清洗操作配方或安全许可

下一步若按既定顺序进入T05，只建议研究源强归一化及角谱不确定怎样与本轮材料未知相分离；具体是否启动由协调者依用户授权处理。
