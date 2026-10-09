# 开始解一个 case：给 AI 的交接说明

本文是「让别人（或别的 AI）接手解一个 case」时的操作手册。
它假设你已经有一个装好环境、能打开 Tableau Desktop 的机器。

---

## 0. 一次性环境准备

```bash
cd wow-tableau-problem-solving
python -m pip install -r requirements.txt     # 安装 pinned 的 cwtwb + hyper api
python download_all.py --refresh              # 拉 posts/ 和 dashboards/（生成物，gitignore）
python scripts/desktop/sdk_source.py          # 确认 SDK 版本与 requirements.txt 的 pin 一致
python -m unittest discover -s tests          # 应全部通过
```

`posts/`、`dashboards/`、`dataset/` 都是**生成物且被 gitignore**。
干净检出里它们为空，必须先跑 `download_all.py --refresh` 才有素材。

选 case：见 `docs/unsolved-posts.md`（未解清单，按年份分组）。

---

## 1. 直接复制给 AI 的提示词

把下面整段发给 AI（Paseo 里选 **Case batch fix** profile；或在仓库目录里跑 pi/Claude Code），
只改 `<...>` 里的内容：

```text
在仓库 C:\Users\imgwho\Desktop\project\wow-tableau-problem-solving 里，
按社区协议解一个 WoW case。

目标 case：
- 文章：<文章 URL 或 posts/ 下的文件名>
- 作者工作簿：<Tableau Public URL>
- iteration-id：<YYYY-MM-DD-wwNN-short-slug>
- challenge-year：<YYYY>

必读（按顺序）：
1. AGENTS.md
2. docs/protocols/community-case-contribution-v1.md
3. docs/cross-repo-desktop-workflow.md

硬性要求：
- 一个 case 一个 PR，只改 iterations/<id>/ 和生成的 usage/*.json 索引。
- 遵守阶段边界：分析阶段可以读文章和作者 TWB/TWBX；
  build_replication.py 只能读 case.yaml、analysis.md、inputs/、
  空模板和公开 cwtwb API，绝不能打开/解压/复制作者工作簿。
- 先用当前 released cwtwb 建基线，记录 cwtwb_result（pass|workaround|blocked）。
- Desktop 门禁：python scripts/desktop/build_and_check.py iterations/<id>
  必须返回 LOADED。FAIL 和 UNKNOWN 都算失败，要重试。
- 如果发现可复用的 SDK 缺口，先写进 case.yaml 的 capability_gaps，
  另开 cwtwb PR；不要在解题 PR 里改 SDK。
- 把每个阶段的结果和根因写进 iterations/<id>/analysis.md，不要只留在对话里。

完成前必须跑：
- python scripts/validate_iteration.py iterations/<id>
- python scripts/desktop/build_and_check.py iterations/<id>
- python scripts/desktop/verify_corpus.py    # 必须 LOADED=50 FAIL=0 UNKNOWN=0
- python scripts/case_catalogue.py --write
- python -m unittest discover -s tests
```

---

## 2. 标准步骤（AI 会走这 10 步）

| # | 阶段 | 动作 | 产出 |
| --- | --- | --- | --- |
| 1 | 认领 | `gh issue create`（用 `.github/ISSUE_TEMPLATE/case.yml`） | issue |
| 2 | 建骨架 | `prepare_case.py`（见下） | `iterations/<id>/` |
| 3 | 分析 | 读文章 + 作者工作簿，写 `analysis.md` | `analysis.md` |
| 4 | 建基线 | 用 released cwtwb 构建，记 `cwtwb_result` | `build_replication.py` |
| 5 | 验证 | `verify_replication.py` + acceptance IDs | 证据 |
| 6 | 静态门禁 | `validate_iteration.py`（XSD + 边界 + 元数据） | PASS |
| 7 | Desktop 门禁 | `build_and_check.py` → 必须 LOADED | LOADED |
| 8 | 回归 | `verify_corpus.py` → LOADED=50 FAIL=0 UNKNOWN=0 | 无回归 |
| 9 | 刷索引 | `case_catalogue.py --write` | `usage/*.json` |
| 10 | 提 PR | 一 case 一 PR | PR |

### 第 2 步的完整命令

```bash
python scripts/prepare_case.py \
  --workbook-url "https://public.tableau.com/views/WORKBOOK/VIEW" \
  --iteration-id 2021-01-06-ww01-short-slug \
  --challenge-year 2021 \
  --case-id wow-2021-ww01-short-slug \
  --post-url "https://donnacoles.home.blog/2021/01/06/..."
```

`prepare_case.py` 会把作者工作簿下载到临时目录、只抽取 `inputs/` 数据、写
`inputs/source-lock.json`，然后删掉工作簿——**不会**把作者工作簿放进 iteration。

`--challenge-date` / `--challenge-url` 只在官方挑战日期已验证时提供
（见 `docs/protocols/challenge-date-sources.json`），否则留空。

---

## 3. 两条最容易踩的坑

1. **`--sdk-src` 必须给。** cwtwb 是 editable 安装，写死指向主检出。
   在 worktree 里改了 SDK 却在别处构建，会静默用旧代码。
   `build_and_check.py --sdk-src <cwtwb-wt>/src` 会检测并直接失败。
2. **`UNKNOWN` 不是通过。** 它通常意味着 Tableau 日志里没匹配到进程
   （比如版本没授权、日志轮转、进程转发）。必须重试到确定结果。
   判定原理见 `docs/desktop-log-verdict.md`。

---

## 4. 相关文档

| 文档 | 回答什么 |
| --- | --- |
| `AGENTS.md` | 解题目标、阶段边界、必需产出（自动加载） |
| `docs/protocols/community-case-contribution-v1.md` | 完整贡献协议 |
| `docs/cross-repo-desktop-workflow.md` | 跨仓库迭代 + Desktop 门禁 |
| `docs/desktop-log-verdict.md` | 判定原理与实测证据 |
| `docs/generated-twbx-desktop-load-audit.md` | 历史根因与逐案例记录 |
| `docs/unsolved-posts.md` | 未解 case 清单 |

---

## 5. 已知限制

- Desktop 验证依赖本机 Windows + 有授权的 Tableau Desktop 2026.2，
  CI 上跑不了，是**人工门禁**。
- 每次 Desktop 验证约 10–60 秒；50 个基线案例全量约 10–30 分钟。
- 3 个作者工作簿在 Tableau Public 上返回 404，无法下载：
  `AutomatingtheHIDEFeaturetoyouradvantage`、`FilmFranchises`、
  `TC23-InteractiveDashboardstheWhyandtheHow`。涉及它们的 case 会缺素材。
- 4 个 historical 案例（schema 1.0.0）按仓库策略只读，不在基线内。
