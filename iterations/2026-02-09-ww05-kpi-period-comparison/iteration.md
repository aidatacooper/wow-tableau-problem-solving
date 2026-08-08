# 2026 WW05：KPI 时期比较完整复刻

日期：2026-07-30  
状态：replicated  
case_id：`donna-2026-02-09-1eb979fd64b6`  
workbook_id：`tableau-93c74baea48daf50`

## 1. 问题理解

用户要同时查看指定日期的 Profit Ratio、相对前一天的变化，以及近期、上月同期和
去年同期的趋势。直接使用真实日期作 X 轴会让三个时期彼此错开，无法比较相同的
相对天位置；直接在趋势粒度上计算单日 KPI，也会受到视图维度影响。

## 2. 原 Tableau 解题链

```text
pToday
→ Today Last Month / Today Last Year
→ 将订单日期分为 Recent / Prior Month / Prior Year
→ X-Axis 将三个时期映射到相对日
→ PR Recent / PR Not Recent
→ 同步 Dual Axis 趋势

pToday
→ FIXED PR Today / FIXED PR Yesterday
→ PR Difference
→ Up / Down
→ KPI Card
```

## 3. cwtwb 实现

`build_replication.py` 直接打开本案例的原始 TWBX，保留 datasource、连接、
参数、计算字段和 Hyper 提取，并清空、独立重建视图层：

- 复用原文件的日期参数 `pToday` 和完整计算链；
- 带非空时期过滤、共同相对日轴和同步双轴的趋势 worksheet；
- 显示当前 Profit Ratio、日环比和方向的 KPI worksheet；
- 包含两个 worksheet 和日期参数控件的 Dashboard；
- 独立 TWB 与 TWBX。

现有 cwtwb 0.24.0 API 足以完成必要语义，本案例没有新增公共 API。

## 4. 复刻差异

- 透明自定义 Shape 替换为 Text mark；透明 Shape 只承担排版，不改变 KPI；
- 不逐像素复刻虚线、circle line marker、字体、padding 和 tooltip；
- 不保留用于搭建计算的中间表 worksheet；
- 保留了用户可观察的时期对齐、趋势比较、KPI 值和方向。

## 5. 验证

- 确定性验收与 TWBX round-trip：通过；
- TWBX 包含原案例的 Hyper 提取：通过；
- Tableau Cloud TWBX 发布与可打开性验证：通过，服务端识别 2 个 worksheets
  和 KPI Dashboard，workbook_id 为
  `9ce42bbd-72a6-4246-87e2-6ab7e1052bcd`；
- analyzer：识别 Dual Axis、ParamCtrl、Line、Text、Color 和布局容器；
- cwtwb 全量回归：316 passed，25 skipped；
- 详细结果与输出哈希见 `evidence/validation.json`。

## 6. 最终状态

```text
status: consumed
replication_status: replicated
```
