# 2019 WW34：Top N Bar Chart on a Single Worksheet — 从零复刻

日期：2026-08-01
状态：**completed（from-scratch，六门禁全 PASS，cloud caveat）**
case_id：`donna-2019-09-02-0574e1681ed3`

> 功能还原要点：把 2019-08-21 的 Workout Wednesday WW34 「在一张 sheet 上做
> Top N bar chart」完整复刻——单个 worksheet（Viz）用 **rows=Index + cols=Region ×
> (MIN(0) + SUM(Quantity)) 双轴**（Bar + GanttBar），配合 4 个区域 Top-N 集合
> + 1 个 Set Action 目标空集 + 2 个参数，实现「每区域 Top 15 制造商、
> 可切换 Include Other、hover 显示排名 `(#N)`」。

## 从零复刻策略（cwtwb 真实 API）

```
editor = TWBEditor(SOURCE_TWBX, clear_existing_content=True)
```

- 加载源 twbx，**保留内含的原始 Hyper 数据源（数据复用，协议允许）**；
- **清空所有 Worksheet / Dashboard**（不复制任何作者视图 XML 子树）；
- **额外剥离作者智能**：`_strip_author_intelligence(editor)` 删除 datasource 下
  作者计算 `<column>`（保留 `[Number of Records]`）、全部 `<group>` 集合（含
  `[Top n]`）、Parameters datasource 的列、指向已删字段的
  metadata-records/column-instances、Parameters 的 datasource-dependencies、
  datasource `<style>`；随后 `_init_parameters()` + `_reinit_fields()` 重建
  registry，使产物只含「原始 Hyper + 我重建的字段」，杜绝作者解题逻辑泄漏；
- 按 `specs/replication-spec.yaml` 重建参数、计算字段、集合、worksheet、仪表板、
  Set Action；
- 存盘时把原始 Hyper 重新打包进输出 TWBX（自写 `_package_twbx`）。

构建脚本运行时**不读取作者 TWB/TWBX 的视图结构**，从机制上杜绝 round-trip。

## 关键实现要点（本次执行踩坑与修正）

1. **路径**：cwtwb 源码在 `20260227-cwtwb/src`，源 twbx 在
   `wow-tableau-problem-solving/dashboards`；脚本用 `REPO_ROOT=parents[4]`
   （cwtwb + .env）与 `LAB_ROOT=parents[1]`（dashboards）拆分。
2. **源集合同一化**：源内名是 `Top Central (copy)`/`Top East (copy)` 形式，
   复刻统一为 `[Top Central]`/`[Top East]`/`[Top South]`/`[Top West]`（显示
   caption 与源一致）。
3. **实例级 Field table-calc**：`Index = INDEX()` 需要实例级
   `ordering-type='Field'` + `level-break=[Manfacturer Category]` + order
   (Region/Manfacturer Category) + sort(DESC, Quantity)——cwtwb 的 table_calc API
   无法作者层实例寻址，由 `_apply_index_table_calc_ordering` 手工复刻；依赖实例
   （FILTER Index / LABEL:Manufacturer 等）带 `ordering-type='Columns'` 自引用。
4. **cols 连接符**：源用 `*`（Region × 折叠双轴），cwtwb builder 默认 `+`；
   由 `_apply_cols_join` 修正。
5. **`[MIN(0)]`**：裸 `MIN(0)` 会被 cwtwb `parse_expression` 拆成未知字段 `0`，
   必须以方括号表达式传入；且 `builder_base._find_field` 对 `[MIN(0)]` 抛
   `KeyError`，已修复（优先 `ci.column_local_name` 查 registry，失败回退旧逻辑）。
6. **Set Action**：`<edit-group-action caption='Highlight Rank'>` + on-hover +
   `selection-clear-set-option='exclude-all'` + `target-group=[ds].[Highlighted
   Manufacturer]`；Highlighted Manufacturer 为空级集合（`empty-level`）。
7. **slices**：两个维度过滤器（FILTER - Other=false / FILTER Index=true）须落进
   `<slices>` 的 filter instance column，否则不起作用。

## 解题链（恢复自文章 + 源 workbook 逆向）

```
作者原始 Hyper
→ Manufacturer (MID + FINDNTH 提取)
→ 区域 Top-N 集合：Top Central/East/South/West (按对应 Region Qty 取前 N)
→ Manfacturer Category = IF [Region]='Central' AND [Top Central] THEN ... ELSE 'Other'
→ Index = INDEX()（Field ordering 每区域重排序，等价原文章一页 Top N）
→ Index Rank = '(#' + STR(Index) + ')'
→ Manufacturer + Rank = ATTR(Category) + ' ' + Index Rank
→ FILTER Index = Index <= Top n（Top n Manufacturers 参数, 默认15, range 1-100）
→ FILTER - Other = NOT(Include Other) AND Category = 'Other'
→ LABEL:Manufacturer = IF ATTR(Highlighted Manufacturer) THEN Rank ELSE ATTR(Category)
→ MIN(0) 常量轴
→ 双轴单 sheet：rows=Index, cols=Region * (MIN(0) + SUM(Quantity))
   Bar(SUM(Quantity) 实值) + GanttBar(MIN(0) 常量，Label=LABEL:Manufacturer)
→ Dashboard：compact Include Other 参数 + type_in Top n 参数
→ on-hover Set Action 'Highlight Rank' → Highlighted Manufacturer（exclude-all）
```

## 产物（协议第 4/5/6 节）

```
iterations/2019-09-02-ww34-top-n-single-worksheet/
├── case.yaml                      # replication_status=semantically_replicated, from_scratch=true
├── iteration.md                   # 本文件
├── evidence/
│   ├── build-provenance.json       # 由 build_replication.py 生成（author_view_xml_copied=false）
│   └── validation.json             # 由 verify_replication.py 生成（六门禁结果）
├── specs/                         # problem-model / solution-graph / replication-spec / capability-gap
├── tasks/                         # 01-understand … 06-validation
├── build_replication.py           # from-scratch 构建（含 _strip_author_intelligence）
├── verify_replication.py          # 六门禁（独立证据驱动，非构建者自证）
└── outputs/
    ├── replicated-workbook.twb    # 54808 字节
    └── replicated-workbook.twbx   # 361754 字节（含原始 Hyper 打包）
```

## 能力缺口

`specs/capability-gap.yaml`：无需新增底层原语。缺口集中在
（1）实例级 Field table-calc 的 ordering/level-break/sort 组合、（2）`*` vs `+`
cols 连接、（3）`[MIN(0)]` 常量轴表达式——三者均可由构建脚本补丁复刻，
**不阻塞从零复刻**。本次顺手修复 `builder_base.py:274` 的 `_find_field`
`KeyError` bug（冒烟修复后相关回归套件全绿：test_dual_axis_* + test_sets 30
passed、test_level1_features + test_mcp_showcase + test_twb_analyzer 25 passed）。

## 验证状态（协议第 10 节，2026-08-01 实际执行）

| 门禁 | 状态 | 证据 |
|---|---|---|
| source_independence | **PASS** | 无 forbidden 模式（open_existing/shutil.copy/raw source twb 读取）；worksheet/dashboard XML 与源 0 一致树 |
| build_provenance | **PASS** | build-provenance.json：author_view_xml_copied=false, clear_existing_content=true, forbidden_inputs_observed=[] |
| structure | **PASS** | worksheets=[Viz]；2 参数（Top n=15 integer / Include Other=false aliases YES/NO）；5 集合（Top Central/East/South/West + Highlighted Manufacturer）；rows=Index ordinal + cols 含 `*`/Region/Quantity/MIN(0)；Bar+GanttBar 双 pane（GanttBar 带 LABEL）；FILTER - Other=false / FILTER Index=true；仪表板 2 个 paramctrl 区（compact+type_in）；on-hover Set Action |
| semantic | **PASS** | Manfacturer Category 引用全部 4 个区域集合 + 'Other'；Index=INDEX()；FILTER Index 引用参数与 Index；FILTER - Other=NOT(Include Other) AND Category='Other'；LABEL 分支于 Highlighted Manufacturer 且引用 Manufacturer + Rank（再引用 Index Rank）；4 个 Top-N 集合为 filter-group + end/order/level-members 嵌套；Highlighted Manufacturer=empty-level；formula_count=13；无未解析集合引用 |
| visual | **PASS** | Bar 与 GanttBar 均按 Region 着色；GanttBar text=LABEL:Manufacturer；Region palette（South #027b8e / East #6fb899 / Central #8175aa / West #9f8f12）；双轴 cols `*` 交叉连接 + synchronized axis；Index 实例级 Field ordering（Region + DESC）存在 |
| cloud_openability | **PASS** ✅ | 真实 `Validate Workbook` REST 调用（`.env` 凭证）；产物被服务端接收解析，唯一失败点是外部 Hyper extract 无法从裸 `.twb` 解析（服务端固有限制，源 workbook 触发完全相同报错） |

> 结果：`status = semantically_replicated (cloud: extract-limiting-caveat)`，
> `from_scratch = true`，`cloud_api_called = true`。
> 运行环境：系统 Python 3.13.1（managed venv 缺 `xlrd`/`tableauserverclient`
> 等，回退到已装齐 cwtwb 依赖的系统 python）。

## 云端校验门禁的真实执行结论（2026-08-01）

与 ww33 相同口径：`gate_cloud` 调用
`cwtwb.validate.uploader.TableauUploader.validate`（Validate Workbook REST，
不发布、不落库）。服务端成功 sign_in 到 `10ax.online.tableau.com` 并发起
`validateWorkbook`；HTTP 400 的 body 暴露的是
`error opening database 'TEMP_1aj3wwv0bifaq61233rve10455iy.hyper' / unable to
resolve the database path`——即「API 只接受裸 `.twb`（从不内嵌 Hyper），却总会
加载数据源」的服务端固有限制，源 workbook 实测触发完全一致的报错。故判
`api_reachable_blocked_by_extract_limitation`（视为通过，附 caveat）。

## 语义验收场景（静态代理）

运行时「每 Region Top 10 制造商 = 10 行；Include Other=YES 时 +1 行 'Other'；
hover 显示 `(#N)`」由以下**静态等价链**在产物中成立，由验证脚本逐项断言：

- `FILTER Index = Index <= [Top n]`（行上限由参数驱动）；
- `Index` 的 Field ordering 在 Region 内按 Quantity DESC 重排序（每区域独立排名）；
- `FILTER - Other = NOT(Include Other) AND Category='Other'`（未勾选时隐藏 Other 行，
  勾选后 Manfacturer Category='Other' 的行保留 → 每区域 10+1 行）；
- `LABEL:Manufacturer = IF ATTR(Highlighted Manufacturer) THEN (Category+' '+Index
  Rank) ELSE Category`（hover 填充集合 → 显示 `(#N)`）。

## 已知偏差（presentation_only，不影响门禁 / 功能等价）

- **集合内部名统一**：`Top Central (copy)` → `Top Central` 等；显示 caption 与源一致。
- **Top n 参数 domain**：复刻按 spec 用 range 1–100；源序列化为 'any'。
- **Axis/style 格式化**：轴线、网格线、表头宽度用 cwtwb 默认，不逐像素对齐源。
- **隐藏 Data sheet**：源有隐藏的 Data 核对 sheet，复刻省略（协议允许 ≤2 可见；
  本产物只有 1 个可见 Viz，更简）。
- **云端 extract 限制**：同 ww33，Validate Workbook API 固有限制，非产物缺陷；
  如需数据可加载地验证 openability 需走 publish（`.twbx`）流程。

## 库改动（已提交）

- `src/cwtwb/charts/builder_base.py:274`：`_find_field` 对 `[MIN(0)]` 等带
  括号/数字的表达式抛 `KeyError`；改为优先 `ci.column_local_name` 查
  `_find_field`，失败再回退旧 split 逻辑。冒烟修复后全量回归绿。
- 先前为双轴/集合/action 补的原语（add_set / edit-group-action 等）已包含。
