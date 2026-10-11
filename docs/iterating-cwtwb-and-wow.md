# 长期迭代 cwtwb 和 wow：简版

两个仓库的长期迭代现在是可行的。本文只讲**怎么做**，不重复原理。

- `cwtwb` = SDK（`C:/Users/imgwho/Desktop/project/cwtwb`）
- `wow` = case 仓库（`C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving`）

凭证已经统一：**两个仓库读同一个文件** `~/.config/wow-cloud/tableau.env`，
不需要 `source`，不需要配环境变量。详见
[wow/docs/tableau-cloud-credentials.md](../wow-tableau-problem-solving/docs/tableau-cloud-credentials.md)。

---

## 一、只想解 case（不碰 SDK）

```bash
cd C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving
git checkout main && git pull --ff-only
git checkout -b feat/<YYYY-wwNN-slug>

# 解 → 构建 → 验证 → 抓 Cloud 证据 → 跑门禁
python scripts/case_intake.py "<文章URL>"          # 定身份
python scripts/validate_iteration.py iterations/<id>
python scripts/desktop/check.py iterations/<id>/outputs/replicated-workbook.twbx   # 必须 LOADED
python -m unittest discover -s tests
python scripts/desktop/verify_corpus.py            # 必须 LOADED=50 FAIL=0 UNKNOWN=0

git push -u origin feat/<YYYY-wwNN-slug>
gh pr create --base main
gh pr merge <n> --merge                            # 只能 --merge，不能 squash
```

**顺序很重要**：先构建，再抓 Cloud 证据，最后才跑门禁。
`validate_iteration.py` 会重建工作簿（UUID 变化），重建后证据哈希就失效了。

---

## 二、要改 SDK（cwtwb）再让 case 用上

**必须先在 cwtwb 提 PR 并合并，再更新 wow 的 pin。** 顺序不能反。

```bash
# 1) 改 SDK + 测试 + 提 PR
cd C:/Users/imgwho/Desktop/project/cwtwb
git checkout main && git pull --ff-only
git checkout -b feat/<what>
# ... 改 src/cwtwb/... 和 tests/ ...
uv run --with pytest --with lxml --with pyyaml --with openpyxl --with xlrd --with mcp \
  python -m pytest tests/ -q
git push -u origin feat/<what> && gh pr create --base main
gh pr merge <n> --merge
git checkout main && git pull --ff-only
git rev-parse HEAD          # ← 记下这个 commit

# 2) wow 里更新 pin（用上一步的 commit）
cd ../wow-tableau-problem-solving
git checkout main && git pull --ff-only
git checkout -b fix/<case>-<what>
# 编辑 requirements.txt: cwtwb @ git+...@<commit>
# 编辑 case.yaml: cwtwb.tested_commit: <commit>
# 改 builder 用新 API，重建、抓证据、跑门禁（同第一节）
git push -u origin fix/<case>-<what> && gh pr create --base main
gh pr merge <n> --merge
```

**为什么要 `--merge` 不能 squash**：`requirements.txt` pin 的是具体 commit SHA。
squash 会让那个 commit 变成**不可达**，`pip install` 就装不上 SDK 了。

**关键细节**：cwtwb 是 editable 安装，指向 `cwtwb/src`。
本地改了 SDK，wow 的构建会**立刻用上**（`sdk_source.py` 会显示 `git 4cd2c61`）。
但要给 CI/别人用，必须走上面的 pin 流程。

---

## 三、判断"要不要改 SDK"

遇到差异时，先问：**这是这一个 case 的特殊情况，还是一个可复用的能力缺口？**

| 情况 | 做法 |
|---|---|
| 现有 API 用错了 | 改 case 的 builder |
| 现有 API 有 bug | 提 cwtwb bug PR（带最小复现） |
| 缺一个可复用的能力 | 提 cwtwb feature PR（走第二节） |
| 只是这一个 case 的视觉差异 | 在 case 里记录为已知差异 |

判断依据写在 `wow/docs/protocols/community-case-contribution-v1.md`。

---

## 四、长任务怎么做（多 case）

**别把一个 agent 塞满**。用 Paseo 的 profile 拆分：

```bash
paseo run --provider pi --model magpie/workbuddy-ai/deepseek-v4.1-flash \
  --new-workspace worktree --worktree-mode branch-off \
  --new-branch feat/case-ww14 --base origin/main "<解这个 case：<URL>>"
```

或直接在 Paseo 里选 profile：
- 批量解 case → `Case batch fix`
- 复核 → `Review & verify`（不同模型、可识图）
- 卡住了 → `Root cause & plan`
- 只跑门禁 → `Mechanical gates`

**每个单元做完就写一行进度**到 `docs/PROGRESS-<topic>.md`
（模板：`docs/protocols/progress-template.md`）。崩溃后从这里恢复，不要考古会话记录。

已配置的自动化：
- **每 30 分钟**：心跳提醒当前 agent 写进度、该拆就拆、卡住就换诊断 profile。
- **每天 09:00**：独立 agent 巡检两个仓库，把结果追加到 `docs/PROGRESS-daily-watch.md`。
  它只读 + 只写进度文档，**不会**自动 commit/push/merge。

---

## 五、日常检查（一条命令）

```bash
cd C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving
python scripts/desktop/sdk_source.py     # SDK 版本/commit 对不对
python -m unittest discover -s tests     # 83 个测试
cat docs/PROGRESS-daily-watch.md         # 昨天的巡检结果
```

---

## 六、不要做

- 不要读 `hyperd.log`（23MB）、`daemon.log`（10MB）、`*.jsonl`（5–8MB）、
  大的 `.twbx`（最大 91MB）。用 `grep`/`tail`/脚本。
  （`context-guard` 扩展会兜底截断，但别依赖它。）
- 不要 commit 任何 token。
- 不要 squash 合并 wow 的 PR。
- 不要直接 push 到 `main`（两个仓库都开了保护，必须走 PR）。
