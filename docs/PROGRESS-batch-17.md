# 进度：batch-17（2021 起最早未解 case）

> 17 个 case 的批量解题进度。崩溃后先读这里，再去 `git log` / `git status`，
> **不要**考古会话记录。详见 [docs/long-running-tasks.md](../long-running-tasks.md)。

## 状态

- 开始时间：2026-10-11
- 目标：从最早未解 case 起，按时间顺序解决 17 个 WoW case。
- 分支：`feat/wow-batch-2021-part2`（worktree: `C:/Users/imgwho/.paseo/worktrees/209a8v60/feat-wow-batch-2021-part2`）
- 进度文档负责人（agent）：batch-17 orchestrator

## 工作清单（按 article_date 升序，取未解可解前 17 个）

- [x] 01 2021-03-18 ww11 Hans Rosling — `2021_03_17_WW11_Hans_Rosling` — replicated/workaround（commit f283e29；LOADED；verify_corpus LOADED=50 FAIL=0 UNKNOWN=0）
- [x] 02 2021-03-25 ww12 Comparative Quantity — `2021_03_24_WW12_Comparative_Qty` — replicated/pass（LOADED；Cloud CSV 与作者逐位一致；无 FIXED LoD）
- [x] 03 2021-04-01 ww13 % Sub-Orders Profitable — `2021_03_31_WW13_Percentage_Sub-Orders_Profitable` — replicated/pass（LOADED；Cloud CSV 与作者逐位一致）
- [x] 04 2021-04-08 ww14 Market Basket — `2021_04_07_WW14_Market_Basket_Analysis` — replicated/pass（LOADED；Cloud CSV 与作者一致；参数 toggle）
- [x] 05 2021-04-15 ww15 Google Analytics — `2021_04_14_WW15_GoogleAnalytics` — replicated/pass（LOADED；4 个 BAN 与作者一致）
- [x] 06 2021-04-23 ww16 Quick LoDs — `2021_04_21_WW16_Quick_LoDs` — replicated/pass（LOADED；Cloud CSV 与作者一致）
- [x] 07 2021-04-29 ww17 Generation Population — `2021_04_28_WW17_Generation_Population` — replicated/pass（commit f590c8c；LOADED@0.27.1 pin；Cloud 证据已重采）
- [x] 08 2021-05-13 ww19 Map Layers — `2021_05_12_WW19_Map_Layers` — replicated/workaround（commit 1dd8b26 + fe7b333；validate PASS / LOADED；Cloud 绑定 f47ea288）
- [x] 09 2021-05-20 ww20 Date Compare — `2021_05_19_WW20_Date_Compare` — replicated/pass（validate PASS / LOADED@4cd2c61；Cloud 3 个 comparison state 的 BAN CSV 与 oracle 逐位一致）
- [x] 10 2021-05-28 ww21 Favourite Songs — `2021_05_26_WW21_Favourite_Songs` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud CSV 89 首过滤歌曲与 oracle 逐位一致）
- [x] 11 2021-06-03 ww22 Unstructured — `WOWW22-Tableau` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud CSV 分箱与 oracle 一致）
- [x] 12 2021-06-11 ww23 Sales Goal Selection — `2021-06-11-ww23-sales-goal-selection-tool` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud BAN CSV 与 oracle 逐位一致）
- [x] 13 2021-06-17 ww24 Cholera Outbreak — `2021-06-17-ww24-can-you-visualise-the-cholera-outbreak` — replicated/workaround（validate PASS / LOADED@4cd2c61；Vincenty 八泵均值与死亡数逐位一致）
- [x] 14 2021-06-25 ww25 Spine Charts — `2021-06-25-ww25-can-you-make-spine-charts` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud 27 行与 oracle 逐位一致）
- [x] 15 2021-07-01 ww26 Pareto Profitability — `2021-07-01-ww26-profitability-with-dual-axis-charts` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud 副标题 79% / 33% 与作者一致）
- [x] 16 2021-07-08 ww27 Top/Bottom Performers — `2021-07-08-ww27-can-you-find-the-top-and-bottom-performers` — replicated/workaround（validate PASS / LOADED@4cd2c61；Cloud 分位分类与 oracle 一致）
- [x] 17 2021-07-15 ww28 FireSize Map — `2021-07-15-ww28-can-you-build-an-app-to-visualise-wildfires` — replicated/workaround（validate PASS / LOADED@4cd2c61；参数 buffer 地图与作者一致）

## 环境修正（2026-10-12）

- 主检出的 editable cwtwb 在批处理中途从 4cd2c61（0.27.1）漂移到 5c65796（0.29.0a1）。
  所有 case 记录的是 0.27.1 / 4cd2c61，因此**必须**用固定 worktree：
  `C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-4cd2c61/src`
  构建时传 `--sdk-src`，回归时设 `CWTWB_SRC`。不要用裸 editable 安装。
- ww17 已用该 pin 重建并重新采集 Cloud 证据。

## 步骤

<!-- 每行：- [x] YYYY-MM-DD <case> — <结果/证据> -->
- [x] 2026-10-11 基线核对 — main@0e465c2；94 solved / 255 unsolved；SDK editable=4cd2c61（pin=86119c1，二者同源）
- [x] 2026-10-11 建分支 `feat/wow-batch-2021-ww11-ww27`
- [x] 2026-10-11 01 ww11 Hans Rosling — 已复现；见工作清单
- [x] 2026-10-11 02 ww12 Comparative Quantity — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-12 08 ww19 Map Layers — 已复现（validate PASS / LOADED）；SDK pin 4cd2c61
- [x] 2026-10-11 03 ww13 % Sub-Orders Profitable — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-11 04 ww14 Market Basket — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-11 05 ww15 Google Analytics — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-11 06 ww16 Quick LoDs — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-12 09 ww20 Date Compare — 已复现（validate PASS / LOADED@4cd2c61；Cloud 3 状态 CSV 与 oracle 一致；83 tests OK）
- [x] 2026-10-12 10 ww21 Favourite Songs — 已复现（validate PASS / LOADED@4cd2c61；Cloud 89 首过滤歌曲与 oracle 一致；83 tests OK）
- [x] 2026-10-12 11 ww22 Unstructured — 已复现（validate PASS / LOADED@4cd2c61；Cloud 分箱与 oracle 一致；83 tests OK）
- [x] 2026-10-13 15 ww26 Pareto Profitability — 已复现（validate PASS / LOADED@4cd2c61；Cloud 79%/33% 与作者一致；83 tests OK）
- [x] 2026-10-13 16 ww27 Top/Bottom Performers — 已复现（validate PASS / LOADED@4cd2c61；Cloud 分位分类与 oracle 一致；83 tests OK）
- [x] 2026-10-13 17 ww28 FireSize Map — 已复现（validate PASS / LOADED@4cd2c61；参数 buffer 地图；83 tests OK）
- [x] 2026-10-12 12 ww23 Sales Goal Selection — 已复现（validate PASS / LOADED@4cd2c61；Cloud BAN CSV 与 oracle 逐位一致；83 tests OK）
- [x] 2026-10-12 13 ww24 Cholera Outbreak — 已复现（validate PASS / LOADED@4cd2c61；Vincenty 八泵均值/死亡数与作者截图逐位一致；83 tests OK）
- [x] 2026-10-12 14 ww25 Spine Charts — 已复现（validate PASS / LOADED@4cd2c61；Cloud 27 行均值/四分位与 oracle 逐位一致；83 tests OK）

## 已验证的技术事实（可复用）

- cwtwb 无 Pages shelf API → 动画页签用 Year 参数 + Selected Year 过滤替代（capability_gap）。
- `set_hyper_connection(tables=..., relationships=...)` 生成的多表关系，Cloud 返回 403132
  “failed to establish a connection to your datasource”，视图空白（1 条和 3 条关系、
  year 键强制 dimension 均复现）。→ 改为在 builder 里把锁定矩阵物化成单张 `Extract` 表。
- `configure_chart` 的 `AGG(measure)` 轴表达式在该 extract 上渲染为空；
  同一字段声明为 `role=dimension, field_type=quantitative` 即正常渲染。
- dashboard `zone()` 不要设 `background-color`，否则白色 zone 会盖住下层 Year 表。
- 诊断脚本：`scratch/batch17/diag.py <request.json> <out.png>`（Cloud 渲染单个 worksheet，
  空图 = 1586x32）。
- `configure_layered_chart(axis_shelf="columns", fold_axes=False)` 会把两个 measure 放成
  同一 worksheet 的**并排两个 pane**（作者 ww12 的 side-by-side 布局）；`fold_axes=True`
  则叠成双轴。
- `add_dashboard_action(action_type="parameter", source_field=..., target_parameter=...)`
  可直接生成原生 `edit-parameter-action`；`action_type="filter"` +
  `field_mappings={"True": "False"}` 复现作者的 "Unhighlight" 行为。
- `{INCLUDE ...}` / `{EXCLUDE ...}` LoD 公式可通过 `add_calculated_field` 正常写入并校验。
- builder 禁止 raw XML：`validate_iteration.py` 的 sdk_boundary_violations 会拒绝 lxml/etree
  导入和 `editor.root`/`_datasource` 访问；一切都要走公开 API。
- 时长格式：秒 → `(SUM(x)/SUM(y))/86400` + `default_format="*nn:ss"`；
  reference-line 的 label 数字格式用 `configure_reference_line_style({"text-format": ...})`。
- `reference-line` 的 `formula` 只能是 constant/total/sum/min/max/average/median/...；
  要显示 `{FIXED : ...}` 聚合值就用 `formula="average"` + `value_field=<聚合字段>`。
- 连续周轴：`DATETRUNC('week', [Date])` 字段 + `EXACTDATE(...)`（cwtwb 没有 Week-Trunc derivation）；
  `WEEK(Date)` 会把两年压成 53 桶。
- 日期范围过滤用 context filter（`{"context": True}`）保证 LoD 之前生效。
- sheet 切换：把两个 sheet 放进同一个 **vertical layout-flow container**（`weight` 分配），
  空 sheet 会塌缩为 0 高，可见的那个填满区域；两个绝对定位 zone 重叠不会塌缩。
- 参数 toggle：`add_dashboard_action(action_type="parameter", source_field="Measure Names",
  target_parameter=..., aggregation="sum")` 生成原生 edit-parameter-action；
  两个 sheet 各自用 `{"column": "Selected Toggle", "type": "quantitative", "max"/"min"}`
  做门控（bound 写在子元素 **text** 里，不是 attribute）。
- 作者用 data source filter 做 "second order" 时，改用文章给的自包含 LoD
  `{FIXED [Customer ID]: MIN(IIF(...))} = [Order Date]` 更可移植。
- mekko/堆叠图：`configure_layered_chart(axis_shelf="rows", fold_axes=True)` 两个 pane +
  下 pane 的 `axis_style.encodings[].reverse=true` 可复现上下堆叠；`mark_sizing`
  （marks-scaling-on + mark-alignment-right）给变宽柱。
- `configure_layered_chart(sort_mode="computed", sort_field=..., sort_descending=...)`
  支持 sort_field 只挂在 Detail 上的 computed sort；`configure_dual_axis` 的
  `_add_shelf_sort` 则要求 sort_field 必须在 row shelf 上。
- **坑**：`build_and_check.py` 不要加 `PYTHONUTF8=1` 前缀——它内部用 `tasklist`（GBK 输出）
  并以 UTF-8 解码，会 `UnicodeDecodeError`；worktree 默认环境即可。
- BAN 自定义色阶：`configure_worksheet_style(color_style={"field": ..., "colors": [...],
  "center": 0.0, "min": -1.0, "max": 1.0, "num_steps": 2, "reverse": True})`
  会生成 `custom-interpolated` + `color-palette custom=true`。**必须给 min/max**，否则
  Cloud 会按数据域自动归一化，正值也会落回黑色；`reverse=True` 把正值放到 teal 端。
- `configure_chart` 的 `label_runs` 支持 `{"param": "<参数名>"}` run（生成
  `<[Parameters].[Parameter N]>`），与 `{"field": ...}` 混用可拼出
  `(Same Day Last Year: Tuesday, 19 May 2020)` 这类参数化标签。
- 日期字段做 label 时用 `EXACTDATE(Field)` 表达式，否则 registry 的
  `default_view_expression` 会自动包成 `MONTH(...)`（同一月内显示为 1 个点）。
- `configure_layered_chart` 的 Multiple Values pane：`mark_style` 里加
  `mark-labels-mode=range` + `mark-labels-range-scope=table` +
  `mark-labels-range-field=Measure Names` + `mark-labels-range-min=true`
  才能只在「最低的那个 measure」上显示标签（作者用来把标签钉在 -500 点上）。
  `color_map` 传 `{measure: hex}` 时走 `set_datasource_color_palette("Measure Names")`。
- `build_and_check.py` 每次都会重新生成 workbook（UUID/时间戳变化）→ 产物 hash 变；
  **门禁顺序固定为**：catalogue → validate → build_and_check → verify →
  更新 build-provenance.artifact_sha256 → capture_case_cloud（最后绑定）→ unittest。
  任何在 capture 之后再跑 build_and_check 都会使 Cloud 绑定失效。
- `capture_case_cloud.py` 的 `states[].parameters` 可以传参数值（如 `pComparison: 2`），
  同一 workbook 多状态导出 `cloud-{role}-{name}.png/csv`，用于验证参数分支。
- **坑**：custom tooltip 的 run 引用 `EXACTDATE(<date field>)` 会让整个 worksheet 在 Cloud 上渲染为空
  （1586x32）。改用裸日期字段；tooltip 文本会按月聚合，仅属表现差异。
- **坑**：folded dual-axis（`fold_axes=True`）再叠加 `axis_style.encodings` + 行 Detail 字段会渲染为空；
  只用 `axis_style.per_field` 设标题。
- 散点+时间线混排（ww21）：两个 pane 的 measure 都根据 set 成员关系切换语义
  （`IF ATTR([Set]) THEN <date-level> ELSE <song-level> END`），
  并用 `configure_layered_chart(axis_shelf="rows", fold_axes=True, synchronized=True)`；
  running total 的 `table_calc_overrides` 用 `EXACTDATE(Date)` 寻址才单调。
- ww22 regex 分箱：Tableau 内部 `sys_numbin` 不在 SDK 函数目录，写进去也不分箱 →
  用文章同时给出的 `FLOOR([price]/[Bin Size])*[Bin Size]`。
- ww26 表计算寻址：**不要**给这些字段传 `table_calc_overrides`——override 会覆盖 builder 自动生成的
  嵌套 `<table-calc field="[ds].[Calculation_...]">` 依赖元数据，导致累计曲线塌成 100%、副标题显示
  `397100%` / `0%`。只写 field-level 的 `table_calc={'ordering_type':'Field','ordering_field':'[Order ID]'}` 即可。
- Hyper extract 的 `lattitude`/`longitude` 列没有 geographic role（`set_field_geographic_role`
  要求 datasource column，但列不存在）→ 用 `MAKEPOINT([lat],[lon])` 空间字段 + `mark_type="Map"`。
- `add_group(name, source, {group: [members]}, default_value=...)` 生成 `categorical-bin`
  column（`<bin value=...>` + `<value>` children），不是 datasource `<group>`。
- ww23：`add_set(name, 'Sub-Category', members=[...])` 生成原生 datasource `<group>`；
  `add_dashboard_set_action(selection_mode='add'/'remove', clear_option='do-nothing')`
  生成两条 `edit-group-action`（并自动写入 `GroupActionAddRemove`/`SetMembershipControl` manifest）。
- ww23 **坑**：BAN 用的 `INDEX()<=1` 量化过滤器**只能写上限**（`{"column": "Index", "max": "1"}`）；
  同时给 min=1 与 max=1 时 Cloud 不会折叠成单行，BAN 会每个 sub-category 重复一行。
- ww23 **坑**：`label_runs` 里同时放字面量 `"<"`、字段 run、`"> to goal"` 会渲染成 `<<field>>`；
  只用 `{"field": ...}` + `{"text": " to goal"}`。
- ww23：`table_calc` 的行寻址用 `{"ordering_type": "Field", "ordering_field": "[Sub-Category]"}`
  （值必须是带括号的字段名）；`add_calculated_field(..., table_calc=...)` 的 `ordering-field`
  若写成不带括号会被 Desktop 拒绝（`Qualified Name Parse Error`）。
- ww23：多 pane 横向折叠轴用 `configure_layered_chart(columns=[...], axis_shelf="columns", fold_axes=True, synchronized=True)`；
  `measure_values` 的 Bar pane 用 `color="Measure Names"` + `size="Measure Names"` 才能拿到 Measure Values 双 pill。
- ww23：BAN 面板直接放 `label="Multiple Values"`（text encoding）即可，**不要**同时加
  `labels=["Measure Names"]`——加了之后 Cloud 整块渲染为空。
- ww24：`Heatmap`（density）mark 受 Tableau 的 `Heatmap` document-format manifest
  entry 门控。`configure_chart(mark_type="Heatmap")` 只写 mark class 不写 flag，
  Desktop 会以 d2e8da72 拒收（XSD 仍然合法）。修法：builder 里先调
  `editor._ensure_manifest_entry("Heatmap")`（这是公开方法，validate_iteration 不报边界违规）。
- ww24：Tableau `DISTANCE(...,'m')` 用的是 **WGS84 Vincenty**，不是球面余弦；
  球面余弦在 8 个泵里有 5 个会差 1 米，对不上作者截图。oracle 用 Vincenty。
- ww24：`add_dashboard_action(action_type="parameter", source_sheets=[...])` 会报
  "Worksheet lists are supported only for filter/highlight actions" → 参数动作只能
  每张 sheet 写一条。
- ww25 **坑**：`PERCENTILE(x,0.25)` 不在 SDK 的 `_DERIVATION_MAP`/`_AGGREGATE_FUNCTION_RE` 里，
  裸写会被注册成 unknown dimension，绑定它的 worksheet 在 Cloud 上渲染为空（1586x32）。
  修法：`add_calculated_field(..., table_calc="Rows")`（或 `{"ordering_type": "Table"}`）。
- ww25：离散 measure 行 pill 需要 `field_type="ordinal"`，连续轴 pill 用
  `field_type="quantitative"`；同一个 measure 要建两份（作者也是两个 column-instance）。
- ww25：`add_reference_band` 写的是 `<style-rule element="refband">` + `fill-color`
  （不是 refline 的 `fill-below`）。
- ww27 `WINDOW_PERCENTILE` 寻址：按 `Rows` 或单个维度寻址会退化成逐格计算，每行的分位值=自身值，全表都判成 Top → 必须用 `table_calc="Columns"` 跨整表寻址。
- ww27 双轴叠加：`configure_layered_chart(axis_shelf="columns", fold_axes=True, synchronized=True)`；
  Rows shelf 放「隐藏的 Sub-Category + 收缩圆点 + 可见副本」三层嵌套。
- ww27 参数清空复位：`add_dashboard_action(action_type="parameter", clear_behavior="set-value", clear_value="i:12")`。
- `configure_layered_chart` 的 pane 数必须与 `configure_custom_tooltip(pane_index=...)` 一致，否则报错。
- `add_group` 生成的是 `categorical-bin` column（`<bin value>` + `<value>` children），不是 datasource `<group>`。
- ww28 参数 buffer 地图：`configure_chart(mark_type="Map", map_layer_mode="native", map_layers=[...])`；每个 buffer layer **必须**有自己的 `detail`（几何表达式本身），否则几何不解析、地图停在世界尺度不缩放。
- ww28 透明 zoom 环：`configure_worksheet_style(panes_style={"2": {"mark_style": {"mark-transparency": "0", "has-stroke": "false"}}})`。
- ww28 面积→半径：`SQRT(([Acres]*43560)/PI())`（BUFFER 接受距离不是面积）。

## 下一步

1. 01–17 全部完成并提交（ww20–ww28）。**batch 完成**。
2. 无剩余 case；收尾：verify_corpus LOADED=50 FAIL=0 UNKNOWN=0。
   **不要**在本 worktree 并行跑 Desktop，也不要重复解 10+，否则产物与 git 会互相覆盖。

## 阻塞

- 无（但注意：`8e72787` 正在同一 worktree 解 09+，其未完成的 case09 会让
  `case_catalogue.py` / `validate_iteration.py` / `python -m unittest discover -s tests`
  报 catalogue 不一致。这是并行 agent 的中间态，不是回归；不要为此重建已完成 case 的产物。）

## 外部状态

- 分支：`feat/wow-batch-2021-part2`（worktree: `C:/Users/imgwho/.paseo/worktrees/209a8v60/feat-wow-batch-2021-part2`）
- 已开 PR：无（分支已 push 到 origin）
- cwtwb pin：`4cd2c61`（`C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-4cd2c61/src`，0.27.1）
- Cloud 证据是否绑定：**ww11–ww28 全部 17 个 case 均已绑定**（replica hash = 提交产物 hash）

## 最终验收（2026-10-13）

- 17/17 case `validate_iteration.py` PASS。
- `python -m unittest discover -s tests` → 83 tests OK。
- `CWTWB_SRC=<pin> python scripts/desktop/verify_corpus.py` → **LOADED=50 FAIL=0 UNKNOWN=0**。
- 17/17 case 的 Cloud 证据绑定到最终提交产物。
- 结果：16 个 `replicated`（pass/workaround），ww26 一度受阻后由后续 agent 攻克，
  最终全部 `replicated`。

## SDK 缺口上游化（2026-10-13，后续）

batch-17 暴露的可复用 cwtwb 缺口已逐个上游化：8 个 PR（每个一个缺口，均带合成
fixture + XPath 回归测试，`pytest -q` 1015 passed / 25 skipped）：

| 缺口 | PR |
|---|---|
| percentile-not-in-aggregation-map（ww25） | https://github.com/aidatacooper/cwtwb/pull/14 |
| heatmap-mark-needs-manifest-flag（ww24） | https://github.com/aidatacooper/cwtwb/pull/15 |
| table-calc-override-strips-nested-metadata（ww26） | https://github.com/aidatacooper/cwtwb/pull/16 |
| rich-label-angle-brackets-dropped（ww23） | https://github.com/aidatacooper/cwtwb/pull/17 |
| extract-lat-lon-have-no-geographic-role（ww22） | https://github.com/aidatacooper/cwtwb/pull/18 |
| buffer-layer-needs-detail（ww28） | https://github.com/aidatacooper/cwtwb/pull/19 |
| pages-shelf（ww11） | https://github.com/aidatacooper/cwtwb/pull/20 |
| custom-geographic-role（ww19） | https://github.com/aidatacooper/cwtwb/pull/21 |

另有 8 个缺口判定为「无需改码 / Cloud 特有 / 已上游修复」，理由已写入各 case 的
`related_cwtwb_issues` 与 `evidence/sdk-baseline.json` 的 `upstream_status`。

回填约定：`case.yaml` 用 `related_cwtwb_issues: [{key, url, status, note}]`；
`evidence/sdk-baseline.json` 的 findings 用 `upstream_pr` / `upstream_status`。
ww49 / ww07 / ww10 三个旧 case 的 `capability_gaps` 原本记为未解，经核对当前 pin
已全部 resolved，已改写为 `upstream_status: resolved`。

## SDK 缺口上游化完成（2026-10-13）

8 个 PR **已全部合并**到 cwtwb `origin/main`（merge commit `23b1df0`，版本 0.29.0a1）：
PR #14/#15/#16/#17/#18/#19/#20/#21（合并提交依次 2b06fa5 / 6e27e7f / f72652e /
97af7fd / 5a9ddec / 2f4f2de / 898b2d1 / 23b1df0）。

合并过程中 #20/#21 因共用 `docs/case-driven-enhancements.md` 与
`capability_registry.py` 需要 rebase 解冲突（两边都是追加型，保留双方条目）。

### pin-bump（已做）

- `requirements.txt`: `86119c1` → `23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`
  （commit `7750686`）。
- 8 个 case 的 `related_cwtwb_issues.status` 与 `sdk-baseline.json` 的
  `upstream_status` 由 `open` 改为 `merged`，并记录 `upstream_merge_commit`。
- 新 pin 下重跑 gate：**17/17 batch-17 case validate PASS**、**83 unit tests OK**、
  `verify_corpus LOADED=50 FAIL=0 UNKNOWN=0`、catalogue 111 active cases。
- 注意：case 的 `cwtwb.tested_commit` 仍为 `4cd2c61c`（构建时实际使用的 SDK），
  **不回改**——它是产物来源，不是 CI pin。与上次 pin-bump（`04a0f12`）一致。
- 新 pin 的本地检出：`C:/Users/imgwho/Desktop/project/.sdk-pins/cwtwb-23b1df0`。

## 仍然待办（截至 2026-10-13）

1. **237 篇未解 case**（349 帖 − 112 个 iteration）。batch-17 之后最早未解需重新盘点。
2. `2019-12-08-ww49-swap-states` 的 notes 仍写「SDK commit will be locked by the
   coordinating maintainer」，但 case 已 pass 且 pinned；如需要可清理该措辞。
3. recipe 级能力（donut/lollipop/bullet/bump/butterfly/calendar/formatted-table）
   仍非一等原语——属设计选择，不是缺陷，除非有 case 需要才升级。
4. 可选的后续优化：ww25/ww24 等 case 现在可以去掉当初的 workaround（例如
   ww25 的 `table_calc='Rows'` hint、ww24 的 `_ensure_manifest_entry`），改用
   新 SDK 的原生路径。这是**保真度改进**，不是 gate 要求；需重建产物 + 重采
   Cloud 证据，建议单独开 PR。
