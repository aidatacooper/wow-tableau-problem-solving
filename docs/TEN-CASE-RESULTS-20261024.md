# 2026-10-24：新增 10 个已验收案例

本地归档共 349 篇文章（抓取日期 2026-10-09）。按文章 URL、历史文章路径及 `replicated` + `verified/historical` 状态匹配：已解决从 **111 增至 121**，未解决从 **238 降至 228**。剩余 223 篇有工作簿链接，5 篇没有；未检查归档日期之后的新文章。

| 2021 周次 | 案例 | 最终验收 |
| --- | --- | --- |
| 29 | Olympic Schedule | 752 项 Cloud 数据检查 |
| 30 | Streaking | 4,896 项数值检查；补齐日历月份 |
| 31 | Needle in Haystack | 13 个产品及集合、客户数、销售数据一致 |
| 32 | Survey Data | 339 项百分比检查；3 个 REST 状态 |
| 33 | Focused Moving Average | 7,488 项数值检查；3 组窗口参数 |
| 34 | Consecutive Starts | 65,040 项字段检查；7,680 场比赛 |
| 35 | Sales Change | 34 组类别年度数据；修正前景绘制和叠加 |
| 36 | Extract Runs | 209,640 项数值检查；3 个时间窗口 |
| 38 | Net Change | 18,144 项检查；3 个日期范围 |
| 40 | Stacked Bars | 90 项字段检查；3 种类别排序 |

10 个案例均为 `replicated / verified / acceptable_delta`，均有最终工作簿对应的 Desktop **LOADED**、Cloud 截图和数据证据。逐例冻结哈希及门禁结果见 [机器可读验收表](ten-case-verification-20261024.json)。原作者工作簿未修改；复现从空白工作簿、锁定输入和公共 SDK 构建。

集成后的 **83 项单元测试全部通过**。固定 SDK 为 `0.29.0a1 @ 23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`；Desktop 基线回归为 **50 LOADED / 0 FAIL / 0 UNKNOWN**。最终集成再次检查全部案例元数据、XSD、工作簿与 Cloud/Desktop 哈希绑定及构建器/验证器来源哈希。不会用原地重建替换已验收工作簿。

验收范围为 Cloud REST 参数/筛选状态、独立原始数据计算和原生动作定义，未宣称执行浏览器点击。视觉差异逐例记录在 `evidence/visual-review.md`，不宣称像素级一致。

独立复核前五例未发现数据语义缺陷。已修正 WW30 过期的作者归档哈希，验证当前作者归档内的 extract 与锁定输入逐字节相同，并保留旧记录；补充 WW29 按钮静态不可见及标签截断、WW30 同值排序、WW31 标签位置、WW32 标题/页脚/面板结构差异。WW33 的控制名称、对齐和缺失最值文字已在原评审中记录。

后五例由 GPT 独立复核全部默认截图及证据哈希，未发现数值差异。按复核意见为 WW36 增加了可见的 Extract Status 和等待 10 分钟阈值说明，重新通过 Desktop、三状态 Cloud 采集和数据验收；GPT 再次看图确认该问题解决。WW35 缺少列表头的差异已明确记录。最终没有未处理的数据或含义缺陷。

所有案例保留独立分支与提交，并合入本地协调分支 `chore/wow-ten-20261023`。尚未 push 或合入 main。用户原有 `docs/PROGRESS-daily-watch.md` 修改保留。

完整剩余列表：[未解决清单](unsolved-posts.md)。
