# Donna Coles 首次三案例试点：实际迭代记录

日期：2026-07-29
状态：completed_pilot
适用版本：cwtwb 0.24.0
后续协议：`../../docs/protocols/case-replication-v2.md`

## 1. 目的

本次试点使用三个连续案例，验证“文章问题 + 原始 Tableau 文件 → cwtwb 通用
能力 → 自动测试 → 示例 TWBX”的迭代链。它成功验证了能力发现和实现机制，
但没有完整复刻三个原始 Tableau 文件。

按照后续协议 v2 的标准，本次结果应理解为：

```text
三个案例已作为研究证据消费
≠ 三个案例均已完整 replicated
```

## 2. 输入

| 案例 | case_id | workbook_id | 主问题 |
|---|---|---|---|
| A | `donna-2026-02-02-5ebab8421caf` | `tableau-90f17c56b06029af` | 动态选择日期粒度和移动平均窗口 |
| B | `donna-2026-02-09-1eb979fd64b6` | `tableau-93c74baea48daf50` | KPI 当前期、上期和去年同期的趋势对齐 |
| C | `donna-2026-02-15-44019b20eed6` | `tableau-f9dff954fb215221` | 将缺失组合按 0 纳入平均，并通过 Apply 交互更新参数 |

每个案例只对应上表中的一个主 Tableau 文件。原始文件位于：

```text
labs/wow-tableau-problem-solving/dataset/workbooks/<workbook_id>/workbook.twb
```

## 2.1 首次试点的选择与原始设计

试点选择 2026 年连续三个案例，是因为它们的数据格式、Tableau 版本和写作风格
接近，同时覆盖由单图计算到多工作表组合、再到复杂交互的递进难度：

```text
A 动态移动平均
→ B KPI 周期比较
→ C Null、平均值与 Apply
```

原计划不是一次复刻三个完整 Dashboard，而是先验证这条链路：

```text
文章说明 + 原始 TWB
→ 理解 Tableau 能解决的问题
→ 确定性提取 workbook 结构
→ 归一化通用能力
→ 探测 cwtwb 当前覆盖
→ 建立失败测试
→ 实现底层原语
→ 生成示例并验证
```

三个文件的原始规模：

| 案例 | Worksheets | Dashboards | 参数 | 计算字段 | Action |
|---|---:|---:|---:|---:|---:|
| A | 1 | 1 | 12 | 20 | 0 |
| B | 3 | 1 | 5 | 36 | 0 |
| C | 2 | 1 | 8 | 33 | 1 |

试点采用的主要门禁是：

1. 文章、case.json、TWBX 和解包 TWB 必须完整对应；
2. 问题理解阶段不得直接提出 cwtwb 改动；
3. 能力结论必须同时有文章和 TWB 证据；
4. `supported` 必须经过最小生成、保存重开和 analyzer 探测；
5. 实现必须是通用原语，禁止 `create_donna_*` 一类案例专用 API；
6. 输入与输出使用哈希锁定，避免数据变化后继续比较旧结果。

本次实际执行证明这些门禁有效，但也证明“三案例共同驱动一次能力开发”会让
底层能力实现与完整文件复刻脱节，因此后续协议改为一次只处理一个案例。

## 3. 案例 A：动态移动平均

### 问题理解

- 问题：用户需要改变日期粒度和移动窗口，同时保持趋势计算正确。
- 直觉解法缺陷：固定公式只能支持一个窗口；只改变日期显示不会自动改变表计算
  的寻址和窗口。
- Tableau 解题链：参数 → 日期粒度计算 → `WINDOW_AVG`/`WINDOW_MAX`
  → 表计算寻址 → 动态显示范围 → Dual Axis 和 Dashboard 控件。

### 本次完成

- 增加结构化 `table_calc` 元数据；
- 将表计算元数据传播到 worksheet `column-instance`；
- 修复保存重开后的表计算识别；
- 生成动态移动平均示例 TWBX。

### 差异与状态

示例证明了动态窗口和表计算原语，但没有逐项复刻原文件的 12 个参数、完整日期
粒度切换、Dual Axis 和 Dashboard。因此状态为：

```text
partial
```

## 4. 案例 B：KPI 趋势与周期比较

### 问题理解

- 问题：把当前期、上期和去年同期映射到同一个相对时间轴，并同时显示 KPI
  当前值和差值。
- 直觉解法缺陷：直接按真实日期叠加会让不同周期错位；只做日期过滤不能形成
  可比较的相对 X 轴。
- Tableau 解题链：日期参数 → 周期边界 → 日期位移 → FIXED LOD/KPI 计算
  → 双轴趋势 → KPI 卡片与 Dashboard 组合。

### 本次完成

该案例用于确认已有参数、LOD、Dual Axis 和多工作表组合的能力边界，没有生成
一个与原文件一一对应的独立复刻 TWBX，也没有因为该案例新增专用公共 API。

### 差异与状态

```text
partial
```

它是试点的比较和回归案例，不应被描述为已经完成 KPI 原文件复刻。

## 5. 案例 C：Null、平均值与 Apply

### 问题理解

- 问题：没有订单的 weekday 会被 Tableau 省略，导致平均值只除以有订单的
  日期；用户还需要先选择日期，再通过 Apply 更新参数。
- 直觉解法缺陷：单独使用 `ZN()` 只能转换已经存在的 Null，不能创造缺失 mark。
- Tableau 解题链：层级与日期参数 → `INDEX()` 放在 Detail 触发域补全
  → `ZN(COUNTD(...))` 将补出的 Null 转为 0 → Average subtotal
  → Parameter Action/Apply → Dashboard。

### 本次完成

- `add_hierarchy`；
- `enable_domain_completion`；
- `configure_subtotals(..., aggregation="Average")`；
- 原生 Parameter Action 和所需 manifest 声明；
- analyzer、MCP、YAML spec、round-trip 和自动测试；
- 生成 `null-safe-average-with-domain-completion.twbx`。

### 差异与状态

生成文件完成了“缺失组合按 0 进入平均”的核心语义，但没有完整复刻原文件的
日期 Apply 工作表、全部参数、Null/0 差异标记和完整 Dashboard。因此状态为：

```text
partial
```

## 6. 交付结果

本次生成文件统一保存在：

```text
iterations/donnacoles-pilot-v1/outputs/
```

代码发布：

- `c15adb8`：表计算和 Parameter Action；
- `4a39eb3`：层级、域补全和平均小计；
- PyPI：`cwtwb 0.24.0`。

验证：

- 全量测试：314 passed，25 skipped；
- 示例 TWBX 通过本地结构验证；
- Parameter Action 修复后曾通过 Tableau API 语义验证；
- 案例 C 新文件的云端语义验证因连接器要求针对该文件单独授权而未完成。

## 7. 试点结论

有效做法：

1. 文章用于理解“为什么”，TWB 用于证明“怎么做”；
2. Tableau 解法必须拆成通用原语，而不是文章专用函数；
3. 保存重开、analyzer 和 Tableau 校验缺一不可；
4. 数据集必须登记已消费案例，避免重复选样。

需要修正的做法：

1. 同时研究三个案例容易让能力实现与完整复刻脱节；
2. 跨案例组合示例不能证明任一原文件已经解决；
3. “实现底层能力”和“复刻完整 Tableau 文件”必须使用不同状态。

因此后续改为：

```text
一次迭代
= 1 篇文章
+ 1 个主 Tableau 文件
+ 1 个完整复刻 TWBX
+ 1 份迭代记录
```

三个试点案例保留 `consumed` 标记，表示它们已经用于本轮能力研究；其复刻状态
均为 `partial`，不能作为三个完整复刻案例计数。
