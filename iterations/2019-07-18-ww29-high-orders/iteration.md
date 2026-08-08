# 2019 WW29：按月比较订单日均值

日期：2026-07-30
状态：replicated
case_id：`donna-2019-07-18-63877b35d19a`
workbook_id：`tableau-e27da65b4c05126c`

## 1. 问题理解

用户需要判断每个 Segment 的哪些月份，其每日平均订单数高于该 Segment 全时期的
每日平均订单数。直接比较月订单总数会受每月实际有订单天数影响；直接对每日计数
取平均又容易受到视图粒度和缺失日期影响。

## 2. Tableau 解题链

```text
Segment
→ FIXED Count Orders / Count Days
→ Overall Avg Orders Per Day Per Segment

Segment + MONTH(Order Date)
→ FIXED monthly Count Orders / Count Days
→ Avg Orders Per Day Per Segment Per Month

monthly average - overall average
→ Difference / % Difference / conditional color
→ GanttBar positioned at monthly average and sized by Difference
→ field-backed reference line at overall segment average
```

## 3. 必要与可替代内容

- required：原始 Hyper 数据、两层 FIXED LOD、月均与总体均值、Difference、
  GanttBar、reference line、Segment/月布局；
- replaceable：精确颜色、tooltip 文案和标题排版；
- presentation_only：作者署名、边距和逐像素字体。

## 4. cwtwb 能力迭代

原始案例要求一个由字段驱动的 per-pane reference line。现有版本能生成 GanttBar，
但没有 reference line 公共原语，analyzer 还会把它标记为 unsupported。此次迭代
新增 `TWBEditor.add_reference_line`、MCP 工具、能力注册、analyzer 覆盖、测试和
Chart Builder 文档，并把原生 GanttBar 注册为 advanced capability。

## 5. 数据保真

`build_replication.py` 直接打开原始 TWBX，保留 datasource、计算字段、连接和
`Data/Datasources/Orders (Sample - Superstore).hyper`，仅清空并重建视图层。

## 6. 验证

- 确定性验收和 TWBX round-trip：通过；
- 原始 Hyper 打包：通过；
- analyzer：识别 GanttBar、Reference Line、LOD、Color、Size、Text、
  Tooltip 和 Hyper；unsupported 为 0；
- cwtwb 全量回归：320 passed，25 skipped；
- Tableau Cloud TWBX 发布：通过，workbook_id
  `df7a9f71-29fc-4e01-af27-13f03b6e29c2`；
- 云端 Dashboard 截图复核：显示 3 个 Segment、12 个月、正负百分比颜色编码及
  每个 Segment 的总体均值参考线。

首次云端截图为空，由“导入计算字段公式未进入 FieldRegistry，聚合字段被错误绑定
为 SUM”导致。修复 `f6f1403` 后重新生成、发布和截图均通过。

## 7. 最终状态

```text
status: consumed
replication_status: replicated
```
