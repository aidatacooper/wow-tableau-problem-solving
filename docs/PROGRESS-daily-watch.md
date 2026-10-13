# 进度：daily-watch

> 每日仓库巡检（自动化，只读 + 只写本文件）。
> 崩溃后先读这里，再去 `git log` / `git status`，**不要**考古会话记录。
> 详见 [docs/long-running-tasks.md](../long-running-tasks.md)。

## 状态

- 开始时间：2026-10-11
- 目标：让 cwtwb 和 wow-tableau-problem-solving 的长期迭代保持可恢复。
- 进度文档负责人（agent）：daily-watch 自动化

## 步骤

<!-- 每行：- [x] YYYY-MM-DD <仓库> — <结论/异常> -->
- [x] 2026-10-11 cwtwb — main 与 origin/main 同步（86119c1）；存在未提交改动：3 个未跟踪文件（tests/test_kpi_field_collision.py、uv.lock、vendor/tableau-document-schemas/schemas/2026_1/twb_fixed.xsd），未自动处理
- [x] 2026-10-11 wow-tableau-problem-solving — main 与 origin/main 同步（8380b31）；工作区干净；门禁通过：case_catalogue PASS（94 active cases），unittest 83 tests OK
- [x] 2026-10-11 wow-tableau-problem-solving — 无 docs/PROGRESS-*.md，无法与 git log 对账，未补录
- [x] 2026-10-11 分支检查 — 两仓库均无未合并进 main 的分支；cwtwb 2 个、wow 4 个本地分支均已合并
- [x] 2026-10-12 cwtwb — main@5c65796 与 origin/main 同步（0/0）；无未合并分支；仍有 3 个未跟踪文件（tests/test_kpi_field_collision.py、uv.lock、vendor/tableau-document-schemas/schemas/2026_1/twb_fixed.xsd），与 10-11 相同，未处理
- [x] 2026-10-12 wow-tableau-problem-solving — main@0e465c2 与工作分支 feat/wow-batch-2021-ww11-ww27@c563446 均与 origin 同步（0/0）；工作区干净；门禁通过：case_catalogue PASS（95 active cases，--write 后无 tracked 改动）、unittest 83 tests OK
- [x] 2026-10-12 wow-tableau-problem-solving — 进度对账：当前分支 PROGRESS-batch-17.md 记 ww11 完成（f283e29/c563446 均在 log 中，无漏记）；但未合并分支 feat/wow-batch-2021-part2（未 push，7 commits ahead of main）已完成 ww12–ww16 并在其自带 PROGRESS-batch-17.md 中记为 [x]，当前分支看不到这 5 个单元
- [x] 2026-10-12 wow-tableau-problem-solving — 在途未提交：part2 worktree 有未跟踪目录 iterations/2021-04-29-ww17-generation-population/（ww17 进行中，cloud-verification=captured_requires_independent_review）；wow-next-case worktree 有未跟踪 scratch/
- [x] 2026-10-12 分支检查 — cwtwb 本地/远端分支全部已并入 main；wow 未并入 main 的仅 feat/wow-batch-2021-part2 与当前 feat/wow-batch-2021-ww11-ww27（均在途，未自动合并）
- [x] 2026-10-12 cwtwb（复检） — main@5c65796 与 origin/main 同步（0/0）；远端分支全部已并入 main；仍有同样 3 个未跟踪文件，未处理
- [x] 2026-10-12 wow-tableau-problem-solving（复检） — 当前分支 feat/wow-batch-2021-ww11-ww27@c563446 与 origin 同步（0/0）；门禁通过：case_catalogue PASS（95 active cases，--write 后仅本文件为 M）、unittest 83 tests OK
- [x] 2026-10-12 wow 进度对账 — 自 10-11 无新提交，无漏记单元：当前分支仅 ww11（f283e29/c563446，PROGRESS-batch-17 已记）；part2 的 ww12–ww16（a7ad7c1/e23240e/1e2c9ec/21b3b2d/200a08b）仍仅存于未合并分支，未补录
- [x] 2026-10-12 阻塞复核 — cwtwb 3 个未跟踪文件（连续第 3 天）、part2 分支分叉、part2 worktree ww17 未提交目录、wow-next-case scratch/ 均与上次相同，无变化

## 下一步

1. 人工裁决 part2 分支：提 PR 合并（--merge）或把 ww12–ww16 补录回当前分支；确认后再继续 ww17。
2. 复核 cwtwb 的 3 个未跟踪文件（连续第 3 天）。
3. 恢复时先读本文件 + feat/wow-batch-2021-part2 的 docs/PROGRESS-batch-17.md，**不要重做 ww11–ww16**。

## 阻塞

- cwtwb 3 个未跟踪文件仍未处理（tests/test_kpi_field_collision.py、uv.lock、vendor/tableau-document-schemas/schemas/2026_1/twb_fixed.xsd）。需人工确认是提交、忽略还是删除，自动化不处理。
- wow 分支分叉：feat/wow-batch-2021-part2 是 feat/wow-batch-2021-ww11-ww27 的后代，含 ww12–ww16 已完成单元，未 push、未合并；两分支各有一份 PROGRESS-batch-17.md 且内容不一致。需人工决定合并 part2 还是补录到当前分支；自动化不合并、不改写 batch-17 清单。
- ww17 在 part2 worktree 中未提交（证据待独立复核）。恢复前不要重做 ww12–ww16。

## 外部状态

- 分支：cwtwb=main@5c65796；wow main@0e465c2；wow 在途 feat/wow-batch-2021-ww11-ww27@c563446 与 feat/wow-batch-2021-part2@200a08b（本次复检无变化）
- 已开 PR：无新增
- cwtwb pin：requirements.txt 固定 86119c1；本地 editable 为 sdk_source git 5c65796 / version 0.29.0a1
- Cloud 证据是否绑定：ww11（当前分支）已绑定；ww12–ww16（part2）各自带 cloud-verification/independent-verification；ww17 待复核
