# WW41 最终独立只读复核

复核日期：2026-10-28。结论：**在本次明确覆盖的冻结产物、四状态静态渲染和 CSV 数值范围内，未发现确定缺陷。此结论不是全部验收通过。真实双向 hover/离开恢复与交互式参数操作尚未验证。**

## 对象与边界

- Worktree：`C:/Users/imgwho/.t3/worktrees/wow-tableau-problem-solving/t3-b1599e93`。
- Case：`iterations/2021-10-14-ww41-how-much-do-top-sub-categories-contribute-to-sales`。
- HEAD：`bd2c5cb88d3d37aba3709a74c2b41fe32c6ef2e6`。
- 冻结 TWBX：`outputs/replicated-workbook.twbx`，SHA256 `7fa9c8916d330ddd2d79e6ac22fe3bab4ac42ad0a31399571bbb1649ed6d80fb`。
- SDK baseline：`0.29.0a1` / `23b1df0609b0464de5fe4fcd48c7f1ffc3c7392c`。
- 已读仓库 AGENTS 规则、`docs/start-a-case.md`、`docs/long-running-tasks.md`；按 ponytail 技能仅做必要只读检查，没有修改实现。
- 未启动子 agent，未访问 Cloud，未启动 Desktop，未构建或重建任何冻结输出，未修改 case、SDK、catalogue。独立 Hyper 查询在系统临时目录运行，日志留在该临时目录并随目录清理。本报告为唯一持久写入。

## 已确认的证据

1. 实际冻结 TWBX 的 hash 与要求一致。`evidence/cloud-verification.json` 的 8 个 PNG、`evidence/cloud-csv.json` 的 20 个 CSV，逐一重新计算 hash 均匹配；两个清单都绑定当前冻结 workbook hash。
2. 独立查询输入 Hyper 全部 9,994 条原始 `Sub-Category` / `Sales`，用 `Decimal(str(value))` 累计得到 17 类、总额 `2297200.86030000002455175`。与声明 `2297200.8603` 的微小差来自原始 double，不影响任何显示数字。未导入 builder、未用其 oracle 作为真值。
3. 对 N=1、5、16、17 的每份 Highlight Table CSV，逐条核对 17 个详情行的销售额（按画面整美元精度）、全局 `Sales Rank`、`Rank Prefix` 与所属组；均吻合独立原始数据。四状态全局 rank 均为 1..17，没有分组重启。全部 subtotal 的可见 `Rank Prefix` 为空，销售额正确。
4. 对四份 Contribution Pie CSV，内层按组销售与外层 17 类销售、类别顺序均吻合独立累计。两 pane 的 TWB `wedge-size` 都绑定 `SUM(Sales)`，没有作者重复 LOD 的行数加权。四份 Summary CSV 的动态文案正确。
5. 作者四份 Data CSV 的 17 类销售与 replica 在显示精度上逐项一致；作者 workbook 不是本复核的数值真值。
6. 目视当前四份 `cloud-replica*.png`：贡献 summary 没有裁切，排名和美元数清晰；类别颜色在外环与表中对应，表内销售递减；N1/N16 单元素分组 subtotal 不显示排名，N17 单组正确显示总销售。N16 的非零 ALL ELSE 仍有细小扇区，100% 文案是预定整百分比舍入。

| N | Top sales（原始精度约值） | Rest sales（原始精度约值） | 可见 summary | 可见 subtotal（整美元） |
| --- | ---: | ---: | --- | --- |
| 1 | 330007.054 | 1967193.8063 | TOP 1 · 14% OF SALES | 330,007 / 1,967,194 |
| 5 | 1292678.03 | 1004522.8303 | TOP 5 · 56% OF SALES | 1,292,678 / 1,004,523 |
| 16 | 2294176.5803 | 3024.28 | TOP 16 · 100% OF SALES | 2,294,177 / 3,024 |
| 17 | 2297200.8603 | 0 | TOP 17 · 100% OF SALES | 2,297,201（唯一组） |

## 排名与 action 专项

- `build_replication.py:54` 的 Rank Prefix 用详情 partition 的 SIZE 与固定类别数区分 subtotal；`:82`、`:83`、`:85` 分别配置 Sales Rank、自身 SIZE、nested Sales Rank 的 Field 寻址。已直接检查冻结 TWB，三个 context 均显式按 Group Order、Sales Group、Sub-Category 寻址。
- CSV 中 subtotal 的未显示 `Sales Rank` 列仍可能重算出 #1/#2，这是 Tableau subtotal partition 的结果。`build_replication.py:86` 可见 label 只组合 Rank Prefix 与 Sales；四状态 Rank Prefix 为空且 PNG subtotal 没有这些排名。因此没有据此认定缺陷。
- `build_replication.py:124` 至 `:127` 的唯一 dashboard action 在冻结 TWB 中是 `tsc:brush`、`on-hover`、`auto-clear=true`，以 Sales Group 匹配。source 排除 Contribution Summary，target 的 exclude 也为 Contribution Summary；dashboard 仅含另外两张业务视图，因此静态作用域恰为 Contribution Pie 与 Highlight Table，没有过滤 action。

## 未覆盖及交接

- 当前 MFA 障碍下，没有执行真实鼠标 hover、双向高亮、移出恢复、subtotal hover 或参数控件操作。REST 参数化截图只能证明各请求状态能计算/渲染，不能证明浏览器事件链。
- 未运行 Desktop、corpus 或重跑 repository tests；这些是 parent-owned 门禁，本复核不替代它们。
- `case.yaml:51`、`:133`、`analysis.md:145` 和部分 handoff/freeze 文字仍可能保留早期“仅默认渲染/其他状态 pending”的叙述。父任务已说明将统一整理；本次以实际文件 hash 及捕获清单为准，没有改写这些文件。最终提交前应使状态叙述与已完成的静态渲染/CSV证据一致，同时保留真实交互待验收。
- 本复核仅接受功能数值与可读性；没有认定与作者 pixel-perfect matched。贡献摘要位置、色板、字体、subtotal 位置的已知差异仍属于 visual delta。

无可复现确定缺陷条目，因此无 defect severity/file-line/repro 可列。剩余主要边界是真实交互验证，不应将整体结果标为全部通过。
