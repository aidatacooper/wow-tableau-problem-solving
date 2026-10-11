# 长期运行与断点恢复

本文说明如何在这个仓库里安全地跑**长时间、多 case、可中断**的自动化任务，
以及中断后如何无损恢复。

背景：早期一次批量任务在跑到一半时进程原生崩溃
（Windows `0xC0000409`，STATUS_STACK_BUFFER_OVERRUN），**进度全部丢失**，
只能从会话记录里考古重建。根因是上下文过重（单次 `read`/`bash` 拉入
100KB–20MB 的文件），不是任务本身有问题。

---

## 1. 硬性规则：不要把这些文件读进上下文

仓库里有一批"上下文炸弹"。**永远不要**用 `read` 或 `cat` 整份读入：

| 文件 | 典型大小 | 正确做法 |
| --- | --- | --- |
| `hyperd.log`、`iterations/*/hyperd.log` | 2–23 MB | `grep -c` / `tail -n 40` |
| `~/.paseo/daemon.log` | 8–10 MB | 同上 |
| `~/.pi/agent/sessions/**/*.jsonl` | 5–8 MB | 用脚本统计，别读 |
| `dashboards/**/*.twbx` | 最大 91 MB | 用 SDK 或 `unzip -l` |
| `iterations/*/outputs/cloud-*.csv` | 最大 9.5 MB | 用脚本聚合 |
| 整份 TWB XML | 20–200 KB | `grep` 定位，只读片段 |

**通用替代**：把多步操作写成一个一次性脚本（放 `scratch/`），
只 `print` 一小段摘要。这比一条条手敲命令既省上下文又更可靠。

### 兜底保护

`~/.pi/agent/extensions/context-guard.ts` 会自动截断**任何**超过 24K 字符的
工具结果（保留首尾，中间替换为省略标记），所以即使不小心读了炸弹文件，
也不会再把进程压垮。可用 `PI_CONTEXT_GUARD_MAX_CHARS` 调整阈值，
`/context-guard-stats` 查看已拦截量。

---

## 2. 进度文档：让崩溃可恢复

**每完成一个可验证的步骤，就追加一行到一个进度文档。**
这是崩溃后能无损续跑的关键——不要依赖会话历史。

建议路径：`docs/PROGRESS-<topic>.md`（例如 `docs/PROGRESS-cases.md`）。
格式：

```markdown
# 进度：<topic>

- [x] 2026-10-11 ww14 — 像素级一致（0.000%），PR #19 已合并，pin 86119c1
- [x] 2026-10-11 ww32 — 0.039%，证据已绑定
- [ ] 2026-10-11 ww45 — 1.967%，待复核
- 下一步：复核 ww45 的 pane 几何差异
- 阻塞：无
```

要求：

- **每步都写**，不要攒着最后写。
- 记录**可执行的下一步**和**当前阻塞**，而不只是"做了什么"。
- 记录 PR 号、commit、pin 这类**外部状态**，因为崩溃后本地 git 可能也丢了上下文。

恢复时：先读进度文档，再读 `git log`/`git status`，**不要**去考古会话记录。

---

## 3. 自动拆分：什么时候该起子 agent

Paseo 的 profile 就是为拆分准备的。判断标准：

| 情形 | 动作 |
| --- | --- |
| 同类任务 ≥3 个（如多个 case） | 每个一个子 agent，用 `profile_case_batch_fix` |
| 需要独立复核 | 起 `profile_review_verify`（**不同模型**，可识图，用于比对渲染图） |
| 卡住 / 反复失败 | 起 `profile_root_cause_plan`（max thinking），产出计划而非直接改 |
| 只是跑门禁 / 刷索引 | 用 `profile_mechanical_gates`（低成本） |

拆分要点：

- **一个子 agent 只做一个 case / 一个 PR**，避免上下文互相污染。
- 子 agent 必须**自己写进度文档**（profile notes 已要求）。
- 复核必须换模型（当前 `profile_review_verify` 用
  `opencode/mimo-v2.6-flash-free`），否则等于自己复查自己。
- 用 `notifyOnFinish` 异步等待，不要阻塞轮询。

---

## 4. 长任务检查清单

开始前：

- [ ] 任务能拆成**独立的、可验证的**单元吗？拆了再开始。
- [ ] 进度文档路径定了吗？（`docs/PROGRESS-<topic>.md`）
- [ ] 已知的大文件清单确认过了吗？（见第 1 节）

执行中：

- [ ] 每完成一个单元，追加进度行。
- [ ] 每个单元跑完该跑的门禁（见 `AGENTS.md` Verification）。
- [ ] 不把大文件读进上下文；需要时写脚本。
- [ ] 上下文快满时（footer 显示），先写进度再继续。

崩溃后：

- [ ] 读进度文档 → `git log`/`git status` → 从"下一步"继续。
- [ ] **不要**从头重做已完成的部分。

---

## 5. 相关文档

| 文档 | 回答什么 |
| --- | --- |
| `AGENTS.md` | 解题目标、阶段边界、必需产出、门禁 |
| `docs/start-a-case.md` | 单个 case 的完整操作手册 |
| `docs/cross-repo-desktop-workflow.md` | 跨仓库迭代 + Desktop 门禁 |
| `docs/tableau-cloud-credentials.md` | Cloud PAT 存放与加载 |
| `docs/protocols/community-case-contribution-v1.md` | 贡献协议（一 case 一 PR） |
