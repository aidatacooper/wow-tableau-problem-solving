# 跨仓库 Desktop 验证工作流

XML/XSD 通过不能证明 Tableau Desktop 能打开；`LOADED` 也不能证明交互正确。
SDK 修复必须依次验证结构、加载、业务行为，最后对完整 case 验收。

例如，指定 Web Page 目标的 URL action 除了 `url-action-type` 和
`url-action-target`，还需要 `SpecificWebTargetsForActions` manifest 声明。
缺少声明时静态 XSD 可能通过，但 Desktop 会拒绝加载。新增原生 XML 能力时，
同时核对作者文件的功能声明，并给生成器添加声明存在性回归测试。

`mark-line-pattern` 同样需要 `PatternedLineMarks` 声明，缺失时 XSD 仍可能通过。
SDK PR #25 已在
`bbd749f25a5375889a66a8cd72aaaee129810353` 合并通用修复，现已包含在本仓库
最终 a4 源码 pin 中；已发布的 PyPI `0.29.0a3` 不包含它。来源区别见下述 SDK
迭代流程；版本号相同不能证明代码相同。

## 1. 固定本次 SDK 来源

先按 [SDK 迭代流程](iterating-cwtwb-and-wow.md) 区分 stable、prerelease 和
fresh main。修改前保存 stable 基线，或任务明确指定的源码基线并记录完整 SHA；
后续运行逐次追加，不覆盖旧结果，不把源码基线记作 PyPI stable 测试。
requirements pin 与 editable 安装都不自动代表“最新”。

源码检出示例（PowerShell；路径替换为实际选定的 SDK）：

```powershell
$env:CWTWB_SRC = 'C:/path/to/selected-cwtwb/src'
$env:PYTHONPATH = $env:CWTWB_SRC
python scripts/desktop/sdk_source.py --expect selected-cwtwb
git -C C:/path/to/selected-cwtwb rev-parse HEAD
git -C C:/path/to/selected-cwtwb status --short
```

在同一专用 shell 中运行 validator、builder、verifier，确保子进程继承选择。
`CWTWB_SRC` 供 SDK resolver 使用；`PYTHONPATH` 也供直接 import 的脚本使用。
包发行测试则在独立虚拟环境安装确切版本，清除这两个覆盖变量，再用
`sdk_source.py` 检查真实 import 路径/版本；其 `selected_by` 标签不能证明
包的发布渠道。记录包 hash，Git SHA 写不适用。

`build_and_check.py --sdk-src <checkout>/src` 对该调用选择并断言 SDK 路径；
它不会替其他独立命令设置环境。`sdk_source.py --expect` 是路径子串断言，
还须核对实际输出。保存完整 SHA、版本、来源、dirty 状态及必要的 diff，
不要仅凭脚本打印的短 SHA 判定可复现。

## 2. 工具与证据边界

| 工具 | 做什么 / 不证明什么 |
| --- | --- |
| `scripts/validate_iteration.py <case>` | 元数据、phase boundary、重建、XSD 与 case verifier；不是 Desktop 交互验证。 |
| `scripts/desktop/build_and_check.py <case> --sdk-src <src>` | 选 SDK、重建、检查打开；`--skip-desktop` 只证明构建，不能当加载通过。 |
| `scripts/desktop/check.py <twbx>` | 打开已有工作簿，不重建；退出码 0/1/2 对应 LOADED/FAIL/UNKNOWN。 |
| `scripts/desktop/check_batch.py <a.twbx> <b.twbx>` | 顺序检查已有工作簿。 |
| `scripts/desktop/verify_corpus.py` | 打开清单中的已有产物，不选 SDK、不重建。 |
| `scripts/desktop/sdk_source.py` | 显示实际导入路径与版本，辅助核对 SDK。 |

默认回归清单为 `scripts/desktop/desktop_baseline_cases.txt`。
要求每个清单项 LOADED，FAIL/UNKNOWN/NOBUILD 均为 0；数量取清单，不写死。
SDK 回归不能只打开用旧 SDK 生成的文件。

Desktop verdict 来自 Tableau 日志：加载结束且无错误对话框为 LOADED，
错误对话框为 FAIL，无法匹配/超时为 UNKNOWN。UNKNOWN 必须排查并重试，
不能改写成通过。脚本会管理 Tableau 进程；同一机器一次只允许一个 Desktop
测试或交互采集任务，开始前协调现有会话，避免打断其他人的操作。
`TABLEAU_EXE`、`TABLEAU_LOG_DIR` 可指定程序和日志位置；记录实际版本与环境。

## 3. 按顺序执行

以下在已显式选定 SDK 的环境内运行：

```powershell
python scripts/validate_iteration.py iterations/<id>
python -m unittest discover -s tests
python scripts/desktop/build_and_check.py iterations/<id> --sdk-src $env:CWTWB_SRC

# SDK 变更：先重建回归清单，再验证已有产物（Desktop 必须串行）
python scripts/desktop/build_and_check.py --cases-file scripts/desktop/desktop_baseline_cases.txt --sdk-src $env:CWTWB_SRC --skip-desktop
python scripts/desktop/verify_corpus.py
```

回归重建放在专用验证检出，避免覆盖其他 case 已绑定证据的提交产物。
记录验证清单、SDK 来源、失败项与日志；缺产物不是可忽略项。
仅 case builder 改动也需按仓库要求检查现有回归基线。

随后对最终 case 产物验证全部 acceptance IDs：数值、筛选、参数切换、
选择/取消、reset 等适用交互，并记录动作、预期与观察。XML 中存在 action
或 filter 只算结构证据；无可执行交互验证时保留 pending/remaining_work。

运行验收实测要点（2026-11-14）：

- Tooltip 必须真实 hover：即使存在 `custom-tooltip` XML，跨 pane 字段仍可能
  不显示。按 F7 进入演示模式可减少界面干扰，逐项核对实际提示内容。
- 数值从 Tableau 工作表菜单 `Copy > Crosstab` 复制运行时 TSV，按显示精度
  比较**全部**预期值，保留剪贴板原始导出和被测工作簿 hash。
  本轮 WW2025 实测为 168/168；其他 case 按自身完整预期集合计数。
- `LOADED` 后 UI 仍不可操作时，检查隐藏的“文件恢复”模态框；用非破坏性的
  `Close` 关闭对话框，绝不删除用户的恢复文件。
- 截图只捕获 Tableau 的 HWND，使用 DPI-aware 的窗口尺寸，不截取整个桌面。

跨 pane tooltip 修复已随 PR #26 合并，requirements 最终 pin 为
`81362658fa1856ce98e86033b05e9f77c6bdad47`（源码 `0.29.0a4`）。
集成人报告实际 WW03 circle tooltip 金额已恢复；这不替代其他 acceptance。
发布快照（2026-11-14）：GitHub prerelease 与 PyPI a4 已公开，pin 保持不变。
集成人确认最终 50 个 corpus 全部 LOADED（源码 `175471…`，与最终 pin 的
Git tree 一致）；公共 PyPI 独立安装的 manifest/tooltip smoke 均通过。
包 hash 与安装证据见 [SDK 迭代流程](iterating-cwtwb-and-wow.md)；
这些结果不替代其他未验证的业务或交互 acceptance。

所有会重建的命令必须在冻结证据前完成；重建可能改变 UUID 和产物 hash。
`case.yaml` 的 `artifacts.primary_workbook` 必须与 builder 默认输出及 verifier
默认输入一致；否则 XSD 可能检查旧产物，而 verifier 检查新候选文件。
最后执行 case 对应的 Cloud/交互/截图采集，记录最终产物 hash。证据冻结后只做
不改产物的检查；`validate_iteration.py --metadata-only` 不重建，也不替代此前
完整验证。若后来重建或改动产物，重新加载、验证行为并采集绑定证据。

## 4. SDK 修复与交接

1. 保存 stable 失败基线（或明确指定的源码基线），检查 prerelease/fresh main 是否仍有缺口。
2. 建 gap 记录：ID、负责人、受影响 acceptance IDs、synthetic 复现、下一步。
   状态为 `identified -> reproduced -> fixing -> upstream merged ->
   case retested -> accepted`。
3. 用无作者数据的测试修复通用 SDK，覆盖适用的 builder、dispatcher、
   public facade、MCP tool 和 capability registry；运行 SDK 要求的检查。
4. 实际创建 issue/PR 后才关联 URL；issue 放 `related_cwtwb_issues`，
   PR 放 gap 记录。尚未创建就明确记录，不能填虚构链接。
5. 本地用明确的 SDK 检出验证；上游合并后，将 WoW pin 更新到可获取的完整
   上游 SHA，并验证安装，再用最终 pin 重跑 case 与回归、追加 run。
6. 完成全部 case 验收与最终证据后，更新状态、gap、进度及生成索引。
   partial/blocked PR 合并不等于 solved，SDK PR 合并不等于 case accepted。

## 5. 并行责任与串行 Desktop

仅在授权且工具可用时委派；无需特定 provider、model 或 profile。
委派说明必须包含文件/case 所有权、SDK 路径/版本/SHA、验收范围、进度文件、
禁止覆盖的改动及集成负责人。没有代理工具就顺序执行。

- 一个文件只有一个写入责任人；独立 case 可以并行分析、构建和跑无 UI 测试。
- SDK 公共实现由一个负责人集成；跨 case 的需求交给该负责人，不同时改同一 API。
- requirements pin、索引、共享进度及最终状态由集成人统一更新。
- 工具支持时可用独立检出隔离文件；共享检出必须严格分配文件，不依赖分支隔离。
- Desktop 进程和日志属于整台机器，所有加载、回归、交互和截图任务必须排队。
- 每个单元交付真实命令/结果、SDK 来源、产物和证据路径、剩余项及下一步。

长任务的大文件与恢复规则见 `long-running-tasks.md`；其中 profile 和自动化配置
示例不作为委派前提。不要假设心跳、巡检或上下文截断扩展在当前环境已启用。

## 6. 最终验收

- SDK 来源可复现，所选基线渠道明确且后续运行均保留；最终 pin 可安装。
- 公共 API 边界、SDK synthetic 测试及 WoW 必需检查通过。
- 当前回归清单全部 LOADED，目标 case 的全部必需业务/交互 acceptance 通过。
- 最终证据对应最终产物 hash，未将结构检查或截图冒充交互验证。
- 元数据与最新 run 一致，真实上游关联及 gap 状态已更新，索引已重新生成。
- 有任何未完成项就保留 partial/blocked 和下一步；只有全题通过才结束解题任务。

参考：`docs/desktop-log-verdict.md`、
`docs/generated-twbx-desktop-load-audit.md`、
`tests/test_desktop_sdk_source.py`。
