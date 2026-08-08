# WoW Tableau AI 案例迭代与任务交接协议（草案）

更新时间：2026-07-30  
状态：draft  
适用范围：WoW Tableau 案例的拆解、理解、能力迭代、复刻、验证和 AI 任务交接

## 1. 背景与目标

本协议用于把一个 Tableau 案例转换为可拆解、可交接、可独立验证的任务系统，使
任意具备文件读取、代码修改和工具调用能力的 AI 都可以：

1. 接手一个案例的完整迭代；
2. 只接手问题理解、结构解析、能力开发、Workbook 构建或验证中的一个阶段；
3. 只接手某个参数、计算字段、Worksheet、Dashboard、Action 或能力缺口；
4. 在不了解全部历史对话的情况下，根据仓库中的任务契约继续工作；
5. 用机器可验证的证据证明完成状态，而不是依赖 AI 的文字声明。

完整流程为：

```text
Source Lock
→ Deterministic Inventory
→ Problem Model
→ Tableau Solution Graph
→ Replication Spec
→ Capability Audit
→ From-Scratch Build
→ Structural Verification
→ Semantic Verification
→ Visual and Interaction Verification
→ Tableau Cloud Openability
→ Consumed + Replicated
```

本协议是在 `case-replication-v2.md` 基础上的扩展草案。v2 继续作为现行协议，
本文件在完成讨论和实现验证前不替代 v2。

## 2. 核心原则

### 2.1 分析原文件不等于复刻原文件

原作者 TWB/TWBX 可以在分析阶段用于恢复解题链，但不能在 from-scratch 构建
阶段作为 Workbook 模板。

以下构建方式属于原文件 round-trip，不属于从零复刻：

```python
editor = TWBEditor.open_existing(author_twbx)
editor.save(output_twbx)
```

以下构建方式才可能满足 from-scratch 要求：

```python
editor = TWBEditor.create(...)
```

或使用经过批准、不包含案例业务结构的空白模板：

```python
editor = TWBEditor.open_template(empty_template)
```

作者原始 Hyper 可以作为数据输入复用。允许复用数据，不代表允许复用作者已经
完成的 TWB XML、Worksheet、Dashboard 或格式结构。

### 2.2 状态必须由证据产生

AI 不得只通过编辑 Markdown 或 JSON 把案例声明为完成。最终状态应由验证程序
根据构建血缘、结构、语义、视觉和 Cloud 证据生成或确认。

### 2.3 分析阶段与构建阶段隔离

分析阶段可以读取文章和原始 TWB/TWBX。构建阶段只允许读取：

- 空白 Workbook 模板；
- 作者原始 Hyper 或其他批准的数据文件；
- `replication-spec.yaml`；
- cwtwb 公共 API 和相关代码；
- 当前任务明确声明的辅助资产。

构建环境不应包含原始 TWB/TWBX，从运行边界上防止整段 XML 被直接复用。

### 2.4 任务交接依赖仓库状态，不依赖对话历史

每个任务必须明确记录：

- 输入；
- 前置条件；
- 允许读取的文件；
- 禁止使用的文件和方式；
- 负责修改的文件；
- 必须生成的交付物；
- 验收命令和判定条件；
- 当前状态和阻塞原因。

任何 AI 接手时，应能只读当前案例控制文件和被分配的任务包开始工作。

## 3. 复刻等级

不再用单一 `replicated` 覆盖不同程度的成果。

| 状态 | 含义 | 是否算完整复刻 |
|---|---|---:|
| `selected` | 已锁定文章和作者主文件 | 否 |
| `analyzed` | 已完成问题理解和原文件解析 | 否 |
| `roundtrip_preserved` | 打开作者文件、修改或重新保存，并保留其结构 | 否 |
| `structure_rebuilt` | 从空 Workbook 重建主要结构，但尚未证明完整业务行为 | 否 |
| `semantically_replicated` | 从空 Workbook 重建完整计算、视图和交互语义 | 是 |
| `visually_replicated` | 语义通过且达到约定的视觉保真标准 | 是 |
| `partial` | 只完成部分必要解题链 | 否 |
| `blocked` | 存在明确且已有证据的阻塞项 | 否 |

建议每个案例同时记录三个正交字段：

```json
{
  "status": "consumed",
  "replication_status": "roundtrip_preserved",
  "from_scratch": false,
  "source_workbook_dependency": true
}
```

`consumed` 只表示案例已经被研究或用于能力迭代，不代表已经完整复刻。

## 4. 案例目录

建议的目标目录结构：

```text
iterations/<iteration-id>/
├── case.yaml
├── iteration.md
├── evidence/
│   ├── source-lock.json
│   ├── workbook-inventory.json
│   ├── build-provenance.json
│   ├── validation.json
│   └── screenshots/
├── specs/
│   ├── problem-model.md
│   ├── solution-graph.yaml
│   ├── replication-spec.yaml
│   └── capability-gap.yaml
├── tasks/
│   ├── 01-understand.yaml
│   ├── 02-calculations.yaml
│   ├── 03-worksheets.yaml
│   ├── 04-dashboard.yaml
│   └── 05-validation.yaml
├── build_replication.py
├── verify_replication.py
└── outputs/
    ├── replicated-workbook.twb
    └── replicated-workbook.twbx
```

不是每个案例都必须产生 `capability-gap.yaml`。只有确认存在 cwtwb 通用能力缺口
时才创建该文件。

## 5. 案例控制文件

`case.yaml` 是一个案例的机器可读控制入口。

示例：

```yaml
schema_version: 1.0.0
case_id: donna-2019-08-14-9a4c743596c1
iteration_id: 2019-08-14-ww33-table-formatting
status: in_progress
replication_mode: from_scratch

inputs:
  article: posts/2019-08-14-Corey’s_Table_Challenge.html
  source_workbook: dashboards/2019_08_14_WW33_Table_Formatting/2019_08_14_WW33_Table_Formatting.twbx
  validation_env: C:/Users/imgwho/Desktop/projects/20260227-cwtwb/.env

constraints:
  preserve_original_hyper: true
  source_workbook_may_be_read_during_analysis: true
  source_workbook_may_be_used_as_build_template: false
  maximum_visible_worksheets: 3

stages:
  source_lock: completed
  inventory: completed
  problem_model: completed
  solution_graph: completed
  replication_spec: completed
  capability_audit: pending
  build: pending
  verification: pending
```

`case.yaml` 只记录控制状态和文件引用，不应重复保存大量文章内容、Workbook XML
或验证日志。

## 6. 标准阶段

### 6.1 Source Lock

锁定并记录：

- `case_id`；
- 文章路径和 SHA-256；
- 作者主 Workbook ID；
- 原始 TWBX 和规范化 TWB 哈希；
- 原始数据文件路径、大小和哈希；
- cwtwb 版本和 Git commit；
- Tableau 验证使用的 `.env` 路径。

该阶段不做业务判断。

### 6.2 Deterministic Inventory

用确定性程序解析作者 Workbook，而不是要求 AI 反复阅读完整 XML。

至少提取：

- 数据源、关系和数据文件；
- 参数和计算字段；
- Worksheet shelves、marks、panes 和 encodings；
- LOD 和表计算；
- filters、sets、groups 和 bins；
- Dashboard zone tree；
- actions 和交互目标；
- 格式、总计、参考线和特殊视觉结构；
- 原始 Workbook 中未被视图实际使用的对象。

输出为 `evidence/workbook-inventory.json`。

### 6.3 Problem Model

AI 只根据当前文章和案例元数据回答：

- 用户最终要做什么判断？
- 普通方法为什么不够或会算错？
- 正确结果必须表现出什么行为？
- 哪些属于必要 BI 语义？
- 哪些属于可替代实现？
- 哪些只是视觉装饰？

这一阶段不讨论 cwtwb API。

### 6.4 Tableau Solution Graph

结合文章和 inventory 恢复：

```text
业务要求
→ 数据域
→ 参数
→ 计算
→ Worksheet
→ Dashboard
→ Interaction
→ Formatting
```

每个节点标记：

- `required`；
- `replaceable`；
- `presentation_only`。

每条边说明上游对象如何影响下游行为。

### 6.5 Replication Spec

把解题链转换为可执行、可验证的构建规格，至少描述：

- 数据连接和原始 Hyper；
- 参数名称、类型和默认值；
- 计算字段的业务角色和公式要求；
- Worksheet 的字段、shelves、marks、panes 和行为；
- Dashboard 的可见 sheets、布局和 controls；
- actions、filters 和参数交互；
- 可观察的验收场景。

示例片段：

```yaml
parameters:
  - name: Highlight Threshold
    datatype: integer
    default: 30

worksheets:
  - name: Table
    panes: 11
    required_marks:
      Bar: 9
      Circle: 1
    behaviors:
      - threshold_highlighting
      - paired_bold_normal_labels

acceptance_scenarios:
  - set_parameter:
      Highlight Threshold: 30
    expect:
      highlighted_rows: formula_driven
```

### 6.6 Capability Audit

按以下分类判断复刻缺口：

- 已有公共原语，可以直接调用；
- 已有能力，但 Agent 不知道如何调用；
- 缺少通用底层原语；
- 缺少可复用组合 recipe；
- 只是视觉差异；
- 原始结构无需一比一复制，可用等价语义替代。

只有确认属于通用缺口时才修改 cwtwb。

公共能力的落地顺序为：

```text
TWB XML primitive
→ TWBEditor API
→ MCP tool
→ capability registry
→ analyzer
→ tests
→ skill/documentation
```

### 6.7 From-Scratch Build

构建必须从空 Workbook 或批准的空白模板开始。作者原始 TWB/TWBX 不得成为构建
输入。

允许：

- 从原 TWBX 提取并复制原始 Hyper；
- 根据 replication spec 创建相同公式；
- 根据 solution graph 创建等价的视图和交互；
- 使用原作者截图作为视觉参考。

禁止：

- `open_existing(author_twbx)` 后直接保存；
- 复制作者 TWB 作为输出起点；
- 从作者文件复制完整 Worksheet 或 Dashboard XML 子树；
- 把作者 TWBX 改名后作为复刻结果；
- 用跨案例演示 Workbook 代替当前案例。

## 7. AI 任务包

一个任务包应当是可单独领取和验收的 YAML 文件。

示例：

```yaml
schema_version: 1.0.0
task_id: ww33-calculations
case_id: donna-2019-08-14-9a4c743596c1
stage: build
status: ready

depends_on:
  - ww33-replication-spec

allowed_reads:
  - specs/problem-model.md
  - specs/solution-graph.yaml
  - specs/replication-spec.yaml
  - evidence/workbook-inventory.json
  - src/cwtwb/

forbidden_inputs:
  - dashboards/2019_08_14_WW33_Table_Formatting/*.twb
  - dashboards/2019_08_14_WW33_Table_Formatting/*.twbx

owned_files:
  - build/ww33_calculations.py
  - tests/test_ww33_calculations.py

deliverables:
  - Highlight Threshold parameter
  - Total Sales for Year and Category FIXED LOD
  - selected-region percentage
  - other-region percentage
  - Highlight boolean
  - paired bold and normal label calculations

acceptance:
  - build starts from an empty workbook
  - expected formulas exist
  - formulas contain no unresolved fields
  - focused tests pass
```

### 7.1 任务包必填字段

每个任务至少包含：

- `task_id`；
- `case_id`；
- `stage`；
- `status`；
- `depends_on`；
- `allowed_reads`；
- `forbidden_inputs`；
- `owned_files`；
- `deliverables`；
- `acceptance`。

### 7.2 任务状态

- `draft`：尚未准备好；
- `ready`：前置任务已满足，可以领取；
- `claimed`：已有执行者；
- `in_progress`：正在工作；
- `needs_review`：交付物已生成，等待独立验证；
- `completed`：通过任务验收；
- `blocked`：有明确阻塞证据；
- `superseded`：已被其他任务替代。

### 7.3 文件所有权

部分任务交给其他 AI 时，必须声明 `owned_files`。执行者只能修改其负责的文件，
不得回退或覆盖其他 AI 的工作。

公共共享文件需要由协调者合并，或者采用单独的整合任务。

## 8. 三种接手方式

### 8.1 完整案例模式

执行者负责从当前未完成阶段一直推进到最终验证：

```text
iterate_case(case.yaml)
```

### 8.2 单阶段模式

执行者只负责一个阶段：

```text
run_stage(case.yaml, stage="solution_graph")
```

### 8.3 原子任务模式

执行者只负责一个明确的任务包：

```text
run_task(tasks/03-worksheets.yaml)
```

每种模式开始前都必须检查：

1. 前置任务是否完成；
2. 输入证据是否存在；
3. 当前任务的文件所有权是否冲突；
4. 原始 Workbook 在当前阶段是否允许读取；
5. 哪些验证门禁决定任务是否完成。

## 9. 能力缺口任务

案例执行者发现 cwtwb 缺口后，应先生成 `capability-gap.yaml`，再由协调者决定：

- 当前执行者继续实现；
- 交给另一个 AI；
- 改用语义等价方案；
- 将案例标记为 blocked。

示例：

```yaml
gap_id: spatial-partitioned-lines
case_id: donna-2019-08-04-a73aff7c512b
classification: missing_primitive

required_behavior:
  - create multiple spatial line partitions
  - preserve path order
  - color partitions categorically

existing_capabilities_checked:
  - configure_map
  - add_spatial_layer

required_layers:
  - xml_primitive
  - editor_api
  - mcp_tool
  - capability_registry
  - analyzer
  - tests
  - documentation

acceptance_fixture:
  data: synthetic
  expected_layers: 2
```

能力实现应使用独立的 cwtwb 提交。案例复刻和能力开发不得混成无法追溯的单一
提交。

## 10. 验证门禁

### 10.1 Source Independence

检查构建脚本和构建进程是否使用了作者原始 Workbook。

静态检查至少识别：

```text
TWBEditor.open_existing(author_twbx)
shutil.copy(author_twbx, output_twbx)
ZipFile(author_twbx)
完整 Worksheet 或 Dashboard XML 子树复制
```

构建完成后，比较源文件和输出文件：

- Worksheet canonical XML；
- Dashboard canonical XML；
- calculation 集合；
- style 和 pane 子树；
- 完全相同的完整子树数量；
- 整体结构相似度。

公式相同本身不是失败，因为正确复刻可能需要相同公式。完整 Worksheet 或
Dashboard 子树直接一致则需要判定是否发生结构复制。

建议输出：

```json
{
  "gate": "source_independence",
  "passed": false,
  "source_workbook_read_during_build": true,
  "identical_worksheet_trees": 4,
  "reason": "The build opened the author TWBX and preserved all worksheet XML."
}
```

### 10.2 Build Provenance

构建器记录实际读取的文件：

```json
{
  "build_inputs": [
    "specs/replication-spec.yaml",
    "data/original.hyper",
    "templates/empty.twb"
  ],
  "source_twb_read_during_build": false,
  "source_twbx_read_during_build": false,
  "forbidden_inputs_observed": []
}
```

### 10.3 Structural Verification

验证：

- 数据源和依赖；
- 参数与计算字段；
- Worksheet、shelves、marks 和 panes；
- Dashboard zone tree；
- filters、actions 和 controls；
- 原始 Hyper 是否存在且哈希或大小符合预期。

### 10.4 Semantic Verification

验证：

- 公式和聚合语义；
- 参数默认值及参数变化；
- filter 和 action 的实际目标；
- LOD、表计算和排序；
- Dashboard 交互后的数据结果；
- 文章定义的正确业务行为。

### 10.5 Visual and Interaction Verification

验证：

- 关键图表是否可见；
- 标题、图例和控制器是否正确；
- 必要的高亮、标记和布局是否存在；
- 参数、筛选器和 action 是否可以实际操作；
- 视觉差异是否仅属于允许的字体、padding 或装饰差异。

### 10.6 Tableau Cloud Verification

使用项目约定的 `.env`：

```text
C:/Users/imgwho/Desktop/projects/20260227-cwtwb/.env
```

完成：

- 上传包含原始 Hyper 的复刻 TWBX；
- 枚举 views；
- 导出必要的 CSV；
- 截取 Dashboard 或 Worksheet；
- 验证可打开性和关键行为；
- 如果使用同名控制文件，验证后恢复最终复刻版本。

本地 XSD 通过不能代替 Tableau Cloud 或 Tableau API 验证。

### 10.7 独立验证

构建执行者不能只凭自己的结果把任务标记为完成。验证应由：

- 独立验证程序；
- 另一个 AI；
- 或协调者执行的只读验收任务

完成。

最终状态示例：

```json
{
  "status": "consumed",
  "replication_status": "semantically_replicated",
  "from_scratch": true,
  "gates": {
    "source_independence": "passed",
    "build_provenance": "passed",
    "structure": "passed",
    "semantic": "passed",
    "visual": "passed",
    "cloud_openability": "passed"
  }
}
```

## 11. Git 与交付

建议继续遵守：

- 一个案例一份独立迭代记录和案例提交；
- cwtwb 公共能力使用独立提交；
- 任务包记录相关提交 SHA；
- 未完成时诚实记录 `partial` 或 `blocked`；
- 不把跨案例演示 TWBX 当成单案例交付物；
- 不提交 `.env`、token 或 Tableau 凭据。

每个任务完成后必须更新自身状态，但只有案例级验证通过后才能更新
`usage/consumed-cases.json` 中的最终复刻状态。

## 12. 对既有案例的迁移

在本协议成为 active 之前，应对现有案例执行一次来源独立性审计：

1. 检查 `build_replication.py` 的起点；
2. 检查构建时是否读取作者 TWB/TWBX；
3. 比较源文件和输出文件的 canonical XML；
4. 确认原始 Hyper 是数据复用还是整个 TWBX 被复用；
5. 按真实证据重新标记复刻等级。

判定原则：

- 从空 Workbook 创建，只复用原始 Hyper：可进入 from-scratch 验证；
- 使用作者 Workbook 作为模板：`roundtrip_preserved`；
- 主要结构从空 Workbook 创建，但部分语义不完整：`structure_rebuilt` 或 `partial`；
- 所有门禁通过：`semantically_replicated` 或 `visually_replicated`。

WW33 已证明需要区分 round-trip preservation 与 from-scratch replication，因此
该门禁不能只依赖执行者自述。

## 13. 待讨论事项

本草案后续需要逐步确定：

1. `case.yaml`、task YAML 和 replication spec 的正式 JSON Schema；
2. 构建 sandbox 的实现方式；
3. Source Independence 的相似度算法和失败阈值；
4. 哪些 cwtwb API 可以合法读取分析结果；
5. 视觉比较的容差和人工复核边界；
6. 多 AI 并行时的文件锁、任务领取和冲突处理；
7. 谁拥有最终状态写入权限；
8. 旧案例迁移是否修改原记录，还是追加审计记录；
9. `semantically_replicated` 与 `visually_replicated` 的最低共同门槛；
10. 如何把协议集成到现有 analyzer、MCP tool 和测试流程。

## 14. 设计结论

这套机制的核心不是给 AI 更多上下文或更长提示词，而是：

```text
机器可读的任务契约
+ 阶段化状态机
+ 分析与构建输入隔离
+ 明确的文件所有权
+ 独立验证门禁
+ 可追溯的构建血缘和证据
```

只要这些约束由文件和验证器执行，其他 AI 就可以接手完整流程或其中任意一部分，
同时降低遗漏、重复工作、越权修改和虚假完成的风险。
