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
- [ ] 05 2021-04-15 ww15 Google Analytics — `2021_04_14_WW15_GoogleAnalytics`
- [ ] 06 2021-04-23 ww16 Quick LoDs — `2021_04_21_WW16_Quick_LoDs`
- [ ] 07 2021-04-29 ww17 Generation Population — `2021_04_28_WW17_Generation_Population`
- [ ] 08 2021-05-13 ww19 Map Layers — `2021_05_12_WW19_Map_Layers`
- [ ] 09 2021-05-20 ww20 Date Compare — `2021_05_19_WW20_Date_Compare`
- [ ] 10 2021-05-28 ww21 Favourite Songs — `2021_05_26_WW21_Favourite_Songs`
- [ ] 11 2021-06-03 ww22 Unstructured — `WOWW22-Tableau`
- [ ] 12 2021-06-11 ww23 Sales Goal Selection — `2021_06_09_WW23_Sales_Goal_Selection`
- [ ] 13 2021-06-17 ww24 Cholera Outbreak — `2021_06_16_WW24_Cholera_Outbreak_Map`
- [ ] 14 2021-06-25 ww25 Spine Charts — `14062017-WW24-SpineCharts`
- [ ] 15 2021-07-01 ww26 Pareto Profitability — `2021_06_30_WW26_Pareto_Profitability`
- [ ] 16 2021-07-08 ww27 Top/Bottom Performers — `2021_07_06_WW27_Top_Bottom_Performers`
- [ ] 17 2021-07-15 ww28 FireSize Map — `2021_07_14_WW28_FireSize_Map`

## 步骤

<!-- 每行：- [x] YYYY-MM-DD <case> — <结果/证据> -->
- [x] 2026-10-11 基线核对 — main@0e465c2；94 solved / 255 unsolved；SDK editable=4cd2c61（pin=86119c1，二者同源）
- [x] 2026-10-11 建分支 `feat/wow-batch-2021-ww11-ww27`
- [x] 2026-10-11 01 ww11 Hans Rosling — 已复现；见工作清单
- [x] 2026-10-11 02 ww12 Comparative Quantity — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-11 03 ww13 % Sub-Orders Profitable — 已复现（validate PASS / LOADED / 83 tests OK）
- [x] 2026-10-11 04 ww14 Market Basket — 已复现（validate PASS / LOADED / 83 tests OK）

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

## 下一步

1. 解 05 ww15 Google Analytics。
2. 剩余 06–17 见工作清单。

## 阻塞

- 无

## 外部状态

- 分支：`feat/wow-batch-2021-part2`（worktree: `C:/Users/imgwho/.paseo/worktrees/209a8v60/feat-wow-batch-2021-part2`）
- 已开 PR：无
- cwtwb pin：`86119c1`（editable 指向 4cd2c61，同源）
- Cloud 证据是否绑定：ww11 已绑定（replica hash 与提交产物一致）
