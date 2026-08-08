# 2019 WW30：可导航 KPI 模块

日期：2026-07-30
状态：replicated
case_id：`donna-2019-07-25-59a0a144b25b`
workbook_id：`tableau-2dde40c2999debb2`

## 1. 问题理解

用户需要在一个紧凑的 KPI 首页中查看 Customers、Products、Orders 和 Cities 四个
去重计数，并能点击任一 KPI 进入对应的 Sales 排名详情，再从详情页返回首页。
普通的四个文本指标不能表达完整任务；案例的关键 BI 行为是跨 dashboard 导航。

## 2. Tableau 解题链

```text
原始 Orders Hyper
→ COUNTD Customer / Product / Order / City-State
→ 4 个独立 Square KPI worksheets
→ 4 Box KPI dashboard
→ 4 个原生 nav-action
→ 4 个按 SUM(Sales) 排序的详情 worksheets
→ 4 个详情 dashboards
→ dashboard-object GO BACK buttons
```

## 3. 必要与可替代内容

- required：原始 Hyper、8 个 worksheets、5 个 dashboards、四项 COUNTD、
  四个 Sales 排名视图、四个 Go To Sheet actions 和四个返回按钮；
- replaceable：精确色板、字体、边距和条形图标签密度；
- presentation_only：作者署名、逐像素排版和装饰性 dummy 色字段。

## 4. cwtwb 能力迭代

原 API 把 Go To Sheet 写成通用 command，不能复刻源文件的原生 `nav-action`，
也没有 dashboard text navigation button。提交 `9076f6a` 增加：

- 原生 `nav-action` 生成并允许 dashboard 作为目标；
- declarative layout 的 `navigation_button` 节点；
- dashboard-object analyzer 识别与 capability registry；
- API 测试和 Dashboard Designer 文档。

## 5. 数据保真

`build_replication.py` 直接打开作者原始 TWBX，保留 datasource、已有计算字段、
连接元数据和 `Data/Datasources/Orders (Sample - Superstore).hyper`，仅清空并
重建视图层。没有替换为 cwtwb 本地 Superstore。

## 6. 验证

- 8 worksheets、5 dashboards、4 nav-actions、4 GO BACK buttons：通过；
- TWBX 原始 Hyper 打包和 cwtwb round-trip：通过；
- analyzer：advanced-fit，unsupported 为 0；
- cwtwb 全量回归（按模块拆分运行）：322 passed，25 skipped；
- Tableau Cloud TWBX 发布并打开：通过，workbook_id
  `76a4c0eb-52ea-4ff4-88b9-e432ff54068a`；
- 云端截图：主视图显示完整 2×2 KPI 点击区；Customer Sales 显示 Sales 排名和
  GO BACK 按钮。

当前 XSD 对原始 2019 extract/layout 元数据给出旧版兼容告警，另含项目已知的
workbook-tail 告警；这些未被误记为 XSD 完全通过。Tableau Cloud 对包含原始
Hyper 的最终 TWBX 完成了解析和可打开性验证。

## 7. 最终状态

```text
status: consumed
replication_status: replicated
```
