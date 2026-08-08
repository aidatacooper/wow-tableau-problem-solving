# 2019 WW31：Hub-and-Spoke 巡演地图

日期：2026-07-30
状态：replicated
case_id：`donna-2019-08-04-a73aff7c512b`
workbook_id：`tableau-29b75742e9f36c7d`

## 1. 问题理解

用户需要把 Ed Sheeran 和 Ben Howard 的演出地点从各自家乡连接成 hub-and-spoke
路线，并按地区拆成三张地图，同时比较两位艺人的地区演出数量、月度趋势和共同
演出艺人。普通点地图只能表达“在哪里”，不能表达从固定起点到每场演出的路径。

## 2. Tableau 解题链

```text
原始 MusicData Hyper
→ Location 分类分组为 Region
→ MAKEPOINT 起点与终点
→ MAKELINE Route + MAKEPOINT Destination
→ 三张按 Region 过滤的双层地图
→ Route 按 COUNTD ConcertID 定大小
→ 两张艺人摘要 + 月度趋势 + Fellow Artist 词云
→ dashboard
→ 两个摘要到词云的 on-hover filter actions
```

## 3. 必要与可替代内容

- required：原始 MusicData Hyper、Region 分组、Route 与 Destination 空间语义、
  三张地区地图、两层独立 geometry、演出数量、摘要、月度趋势、词云和 hover
  过滤；
- replaceable：旧版 dual-axis 地图机制可由现代多 map-layer XML 等价实现；
- presentation_only：精确地图底图、字体、色板、边距和作者署名。

## 4. cwtwb 能力迭代

提交 `a7d6872`、`a6f4eae`、`63f346f` 增加：

- spatial 字段的 Tableau `Collect` 聚合；
- map layer 的字段型 `geometry`，以及每层 label/detail；
- 空间图层基础 pane、重复 longitude axes 和 `map_partition` 分面；
- `MAKEPOINT` / `MAKELINE` 空间图层文档与结构测试；
- 分类分组的 `TWBEditor.add_group`、MCP `add_group` 和 analyzer capability；
- 公共 MCP 导出、回归测试和 Calculation Builder 文档。

## 5. 数据保真

`build_replication.py` 直接打开作者原始 TWBX，保留 datasource、Region 分组、
空间计算与 `Data/Datasources/2019_07_31_PD25_WWPD_MusicData_Output.hyper`，
仅清空并重建视图层。没有替换为 cwtwb 本地 Superstore。

## 6. 验证结果

- 7 worksheets、1 dashboard、3 张双层地图、2 个 hover actions：通过；
- TWBX 原始 Hyper 打包和 cwtwb round-trip：通过；
- analyzer：advanced-fit，unsupported 为 0；
- cwtwb 全量回归：327 passed，25 skipped，8 warnings；
- Tableau Cloud 同名 workbook：
  `a983daa4-7fd2-42b8-b58b-8c19dbe15b0e`；
- 作者原始 TWBX 控制上传可渲染，随后已自动恢复复刻版本；
- 两张摘要、月度趋势、词云和三张空间图均返回非空 CSV 与有效截图；
- 三张空间图 CSV 分别为 81,304、42,130、11,698 bytes；
- 最终 dashboard 截图 246,862 bytes，可见 Artist 分面的 Route 和 Destination。

结论：完整 Tableau 解题链、原始 Hyper、交互和 Cloud 可打开性均通过，
状态标记为 `replicated`。
