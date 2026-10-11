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

## 下一步

1. 下次巡检先复核 cwtwb 的 3 个未跟踪文件是否被有意提交；未确认前保持只读。
2. wow 若开始长期任务，先按 docs/protocols/progress-template.md 建 docs/PROGRESS-<topic>.md，供后续对账。

## 阻塞

- cwtwb 有 3 个未跟踪文件（tests/test_kpi_field_collision.py、uv.lock、vendor/tableau-document-schemas/schemas/2026_1/twb_fixed.xsd）。需人工确认是提交、忽略还是删除，自动化不处理。

## 外部状态

- 分支：cwtwb=main@86119c1；wow=main@8380b31（均与 origin 同步）
- 已开 PR：无新增
- cwtwb pin：wow 的 pin 见 docs/tableau-cloud-credentials.md，本次未改动
- Cloud 证据是否绑定：本次巡检未涉及
