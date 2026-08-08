# 2019 WW32：Step Area Chart

日期：2026-07-30  
状态：replicated  
case_id：`donna-2019-08-09-22359581fc60`  
workbook_id：`tableau-a671a1f433d4dcca`

## 问题理解

在不复制数据集的前提下，用单一主轴绘制 2018 年三个 Category 的阶梯面积图，
并在同步次轴上突出每类最大月度上涨和最大月度下跌。Tooltip 必须给出类别、
月份、Sales 和相对上月变化。

## Tableau 解题链

```text
作者原始 Orders Hyper
→ Category + 月份 FIXED Sales
→ 月初/月末 Month Position 展开阶梯端点
→ LOOKUP 得到下一月值与 Sales Diff
→ WINDOW_MAX / WINDOW_MIN + FIRST / LAST 定位标签
→ Area 主轴
→ 两项 Measure Values 的 Line 同步次轴
→ Colour:Diff 与 Size 强调最大 rise/drop
→ Dashboard
```

## 语义分类

- required：原始 Hyper、月份端点、FIXED LOD、嵌套 table calculations、三 pane、
  Measure Values 次轴、同步轴、最大上涨/下跌颜色和大小；
- replaceable：帮助核对的 DATA 1 / DATA 2 sheets，可保持隐藏；
- presentation_only：精确字体、页脚链接和细微边距。

## cwtwb 迭代

- 从空白 `TWBEditor("")` 开始，只读取锁定的作者原始 Hyper；
- `set_hyper_connection` 新增真实 Hyper schema introspection、字段 metadata 重建和
  TWBX 内 Hyper 打包；
- 新增通用 `configure_layered_chart`，支持任意 pane、`Multiple Values`、
  Measure Names filter/slices、同步轴、每 pane palette 和显隐轴；
- 新增每个 column-instance 独立的 table-calculation addressing override，
  使嵌套 `LOOKUP` / `WINDOW_MAX` / `WINDOW_MIN` 的寻址可由公共 API 表达；
- 修正字符串 table calculation 作为 measure 时必须生成 `usr:` 实例的字段语义；
- 新增公共 `set_worksheet_title`；
- analyzer 继续识别三 pane `Area + Area + Line` 为 `Step Area`。

## 验证

- 来源独立性：构建脚本不调用 `open_existing`，不引用作者 TWB/TWBX；
- 作者与复刻 worksheet canonical XML 无相同树；
- 原始 Hyper SHA-256：
  `9042a661caa6195146adc567c7eaaf8a4471f920946ed9bb96b2a8f1cfc57748`，
  输入文件与生成 TWBX 内数据完全一致；
- 本地结构、Hyper metadata、保存后重开和 acceptance：通过；
- analyzer：识别 `Step Area`；
- Tableau Cloud semantic validation：通过，无 errors/warnings；
- cwtwb 全量回归：334 passed，25 skipped，8 warnings；
- Tableau Cloud workbook：
  `e4473616-a802-4290-a2a7-7a68f1243342`；
- `Viz` 和 dashboard CSV：各 27,079 bytes；
- dashboard 截图：106,500 bytes，显示三类 stepped areas、最大 rise/drop
  蓝红竖线、首末值和差额标签。

结论：完整解题链与可打开性通过，状态为 `replicated`。
