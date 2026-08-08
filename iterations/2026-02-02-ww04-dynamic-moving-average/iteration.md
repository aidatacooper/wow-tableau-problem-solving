# 2026 WW04：动态移动平均完整复刻

日期：2026-07-30  
状态：replicated  
case_id：`donna-2026-02-02-5ebab8421caf`  
workbook_id：`tableau-90f17c56b06029af`

## 1. 问题理解

用户需要在 week、month、quarter 三种日期粒度之间切换，同时改变移动平均窗口
和显示时间范围。普通日期过滤会在表计算之前删除历史 mark，使移动平均失去所需
的前序数据；固定日期粒度或固定窗口也无法满足交互要求。

正确做法是先在完整可见域上计算动态日期、移动平均和最新日期，再使用布尔表计算
过滤仅隐藏显示范围之外的 mark。

## 2. 原 Tableau 解题链

```text
pTimePortion
→ Display Date = DATE(DATETRUNC(...))
→ 按动态粒度形成时间轴

pMoveAvg
→ Moving Avg = WINDOW_AVG(..., -(pMoveAvg-1), 0)

Display Date
→ Latest Date = WINDOW_MAX(MAX(Display Date))

pTimeFrame + Latest Date
→ Date to Display
→ True 表计算过滤

SUM(Sales) + Moving Avg
→ 两条 Line
→ 同步 Dual Axis
→ Dashboard 上方三个参数控件
```

## 3. cwtwb 实现

复刻脚本为 `build_replication.py`。它直接打开本案例的原始 TWBX，保留原始
datasource、连接、参数、计算字段和 Hyper 提取，仅清空并独立重建视图层：

- 复用原文件的 3 个参数及 4 个必要计算字段；
- 一个带 True 表计算过滤器的同步双轴折线 worksheet；
- 一个包含三个参数控件和主图的 Dashboard；
- 独立 `.twb` 与 `.twbx` 输出。

本案例还发现并修复了一个通用 TWBX round-trip 问题：源包已经包含的数据文件
如果同时能从本地连接路径解析，会被再次写入 ZIP。cwtwb 提交
`e401a12` 现在按归档路径去重，并增加了回归测试。

## 4. 复刻差异

允许差异只涉及表现层：

- 使用更明确的 worksheet/dashboard 名称；
- 字体、精确色值、padding 和 tooltip 文案不要求逐像素一致；
- 标题使用稳定说明文字，没有复刻 Tableau Public 发布后会丢失的动态轴标题。

参数、计算依赖、表计算过滤时序、双轴组合和 Dashboard 控件均保留。

## 5. 验证

- 确定性验收：通过；
- TWB/TWBX 本地解析：通过；
- TWBX 打开、保存及再次验收：通过；
- TWBX 包含原案例的 Hyper 提取：通过；
- analyzer：识别 Dual Axis、ParamCtrl、Table Calculation、Line 和布局容器；
- Tableau Cloud TWB semantic validation：独立 TWB 因依赖打包 Hyper 返回 HTTP 400；
- Tableau Cloud TWBX 发布与可打开性验证：通过，服务端识别 1 个 worksheet
  和 1 个 dashboard，workbook_id 为
  `03c2591a-994f-45e3-905a-2623e5bd979e`；
- cwtwb 全量回归：316 passed，25 skipped；
- 输出哈希和完整结果见 `evidence/validation.json`。

## 6. 最终状态

```text
status: consumed
replication_status: replicated
```
