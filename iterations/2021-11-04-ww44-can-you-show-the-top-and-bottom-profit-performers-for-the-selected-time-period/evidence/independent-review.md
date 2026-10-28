# WW44 当前产物独立复核

复核日期：2026-10-28。只读审查 case 与作者归档；未改 case/SDK、未重建 frozen、未运行 Desktop/Cloud、未提交。已读 AGENTS.md、docs/start-a-case.md、docs/long-running-tasks.md，代码审查采用 ponytail 的最小必要检查原则。

## 结论与缺陷

**未发现已确认的业务逻辑、计算、集合、标签、布局或打包代码缺陷。** 当前三种期间的静态 Cloud 画面均显示完整、可读的 3 个 KPI 和 11 个类别及金额；所有类别、顺序、符号和四舍五入金额都与独立原始数据 SQL 一致。没有需按 severity/file/line 上报的 confirmed defect。

支持通过的范围是：原始数据/公式语义、生成 XML 契约、当前冻结包对应的 Month/Quarter/Year REST 渲染。**不支持宣称 live KPI 交互或全体验收已通过。** 浏览器 MFA 未完成，点击、清除选择、多选及 hover 未亲测。最终 Desktop/corpus 与 metadata 整理由父任务负责。

## 审查对象和证据绑定

工作树：`C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-5ae5d48d`。

案例：`iterations/2021-11-04-ww44-can-you-show-the-top-and-bottom-profit-performers-for-the-selected-time-period`。

- 当前包：`outputs/replicated-workbook.twbx`。
- 当前 SHA256：`07a9dd44a79f541786843f19f120f6dedad1e7a276ee6d5c4a1fea80e1af70dd`。
- `evidence/cloud-verification.json` 的 replica source hash 与当前包匹配；其中 6 张 author/replica PNG 的文件 SHA 也逐一验证匹配。
- 已逐张看过当前 default、quarter、year 的 6 张 PNG；图片分辨率均为 1400×1600，对应 700×800 dashboard。
- **没有使用旧 cloud-csv.json 或 runtime CSV 作为当前包证据。** 已知旧 handoff/Desktop/metadata 绑定由父任务刷新，未把它们重复列为代码缺陷。
- SDK baseline 声明为 `0.29.0a1 / 23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`；本复核未调用 SDK builder，未验证安装环境本身。

## 方法

1. 分析阅读归档文章和作者 TWBX 中有针对性的计算、Top/Bottom 原生集合、parameter action。未整读 XML 或 CSV。作者使用 global latest-month FIXED LOD、三个日历期计算、5 records top/bottom、SUM/COUNTD 中间组平均、按正负分流标签、Measure Names→parameter 的 on-select ATTR action、clear do-nothing；当前实现保持这些业务契约。
2. 把当前包、source-lock 和 Hyper 复制到 `scratch/ww44-review-agh3cnz_`，import 当前 verifier 并将 HERE 指向临时副本，执行其 main。成功通过 8 个本地验收契约、3 种期间、3 个故意错误 mutation，以及 2023-05 calendar fixture。生成证据只写临时副本，没有改 frozen case。
3. 另用独立 Hyper SQL，仅从原始 Order Date/Sub-Category/Profit 开始，按 `DATE_TRUNC(period, Order Date) = DATE_TRUNC(period, MAX(Order Date))` 选择期间，category SUM，ROW_NUMBER 降序取 1–5 和 13–17，中间 7 个 AVG，再与 verifier 的 independent Python oracle 对照。所有值、组别、成员数均一致。此 SQL 不读取 builder 计算或预计算数据。
4. 当前 workbook 结构检查覆盖两个 sheet、700×800、三值 Period 参数、原生 set count=5、无提前过滤、排序、两个 synchronized/folded Gantt panes、标签引用、no-tooltip 和动作映射。包内 Hyper 字节哈希与 source-lock 锁定的输入相同，连接相对路径有效。

## 独立数值结果与可见结果

| Period | KPI 原值 | Everyone Else 原值 | 可见整数 |
|---|---:|---:|---|
| Month | 8483.3468 | 422.0875857143 | KPI $8,483；中间 $422 |
| Quarter | 27448.7260 | 1243.2569857143 | KPI $27,449；中间 $1,243 |
| Year | 93439.2696 | 4603.3694285714 | KPI $93,439；中间 $4,603 |

每张图的前三栏始终为 Month / Quarter / Year，金额始终相同。三种图中的 11 行如下，均按值降序显示，名称及金额均未缺失、截断或相互遮挡：

- Month：Copiers 2541、Chairs 2020、Paper 1704、Phones 1681、Storage 1394、Everyone Else 422、Fasteners 62、Machines (40)、Bookcases (367)、Tables (777)、Binders (2690)。
- Quarter：Copiers 11888、Phones 5505、Accessories 4470、Paper 4034、Storage 3278、Everyone Else 1243、Supplies 58、Bookcases (894)、Binders (2199)、Machines (2864)、Tables (4530)。
- Year：Copiers 25032、Accessories 15672、Phones 12849、Paper 12041、Appliances 7865、Everyone Else 4603、Fasteners 305、Bookcases (584)、Supplies (955)、Machines (2869)、Tables (8141)。

正值类别在左、金额在右；负值金额在左、类别在右，贴近对应端点。极小的 Fasteners/Machines/Supplies 行也能读到两个标签。Top 5 为青绿、Bottom 5 为红色、Everyone Else 为灰色。相对 bottom 的正利润成员正确留在 bottom，而非被错误排除。

## 完整 case acceptance 映射

| Acceptance ID | 当前复核结果 | 证据/边界 |
|---|---|---|
| latest-calendar-periods | PASS（计算） | raw MAX=2021-12-30；Month=12-01、Quarter=10-01、Year=01-01；独立 SQL、公式翻译及 2023-05 fixture 通过 |
| all-period-kpis | PASS | 9 个 selected-period/KPI 数值组合不变；三种当前 PNG 均显示相同三个 KPI |
| dynamic-top-bottom-five | PASS（数值及 REST 状态） | 17 类按各期原始 SUM 排名，5+5 无交集；PNG 的三种 membership 与 SQL 一致；点击触发另见 action 边界 |
| middle-seven-average | PASS | 每期 7 类汇为一行且除以 7，总计 11 行；SQL/公式/PNG 一致 |
| signed-labels-and-sorting | PASS（当前三种静态状态） | 降序、零点两侧、负数括号、双端标签均可读；Gantt labels/size/sync XML 检查通过 |
| kpi-action-contract | PASS（契约）；live 未验证 | on-select、正确 dashboard/sheet、Measure Names→Period、ATTR、clear do-nothing 与作者一致；不能证明实际点击/清选行为 |
| ties-and-filter-order | PASS（当前输入/结构） | 各期 17 个数值均不重复；无 date/category 提前过滤；5 records 而非 dense rank；未来边界 ties 运行时选择仍需审查 |
| packaged-data-integrity | PASS | 当前包内 Hyper 与锁定原始输入 byte hash 相同；relative connection；verifier 通过 |
| desktop-interaction-visual-gates | PARTIAL / 未完成 | 当前 PNG 视觉部分可接受；本复核未跑 Desktop/corpus，无 live 点击/hover，因此整项不算通过 |

## 可接受差异与未验证边界

配色、字体、卡片边框、留白、静态通用标题与作者不同，属于当前 PNG 中可见的样式差异；作者标题动态写出期间，replica 标题保持通用。未发现这些差异违反当前 case 的可观察验收条件。可支持 `acceptable_delta` 的静态画面判断，不支持 `matched`。

本复核没有证明：真实用户点击 Month/Quarter/Year 后动作分发成功、清选后保留参数、多个 KPI 选中后的 ATTR 行为、选择高亮、悬停时无 tooltip、Tableau Desktop 加载和全部 corpus 加载。REST 参数注入的三种 PNG 证明公式在对应参数状态下正确，不能替代这些交互门禁。没有把配置了 tooltip-mode=none 等同于实际 hover 已测试。

父任务应在最终报告中保留以上证据范围；在 live 门禁完成前，不能仅凭本报告把全部功能验收判为完成。
