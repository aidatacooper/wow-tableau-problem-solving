# 跨仓库 Desktop 验证工作流

本文记录如何在「解题（wow-tableau-problem-solving）」与「迭代 SDK（cwtwb）」
两个仓库之间安全地迭代，并保证每一步产物都能在 Tableau Desktop 中打开。

适用读者：在本仓库工作的人，以及被委派到本仓库工作的 Paseo 子 agent。

---

## 1. 为什么需要这套流程

这个仓库的验收标准有一条是 XSD 门禁看不见的：

> **生成的 `.twbx` 必须能被 Tableau Desktop 打开。**

`scripts/validate_iteration.py` 会用 Tableau 官方 XSD 校验元素顺序，但有一类
缺陷它查不出来——**manifest 标志缺失**和**元素放置错误**。这类工作簿 XML
完全合法（0 个 schema 错误），Desktop 却会直接拒绝加载，报错码 `d2e8da72`。

历史教训：51 个已提交产物通过旧验收流程，却打不开。原因是「从不真正打开文件」
的验收方式。所以 Desktop 验证必须是一道**显式门禁**，而不是可选项。

另外两个已确认的坑：

1. **`scratch/` 被 gitignore**。验证脚本原本放在那里，导致 Paseo worktree 里
   没有验证工具。本文所述脚本已迁到 `scripts/desktop/` 并纳入版本控制。
2. **`cwtwb` 是 editable 安装，指向单一固定路径**。在 worktree 里构建会静默
   导入主检出的 SDK，而不是你刚改的那个 worktree——改动看起来「没生效」。
   第 4 节给出解决方案。

---

## 2. 三层结构总览

```
┌─────────────────────────────────────────────────────────────┐
│  Paseo：负责「拆分」                                          │
│  project（仓库根）→ workspace（某分支的检出）                  │
│  worktree 隔离 = 每个 agent 一个独立检出，互不干扰             │
└─────────────────────────────────────────────────────────────┘
                            ↓ 委派
┌─────────────────────────────────────────────────────────────┐
│  pi：负责「压缩」与「上下文管理」                              │
│  ~/.pi/agent/settings.json → compaction.*                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ 执行
┌─────────────────────────────────────────────────────────────┐
│  本仓库 scripts/desktop/：负责「Desktop 验证」                 │
│  verdict / check / check_batch / build_and_check /           │
│  verify_corpus / sdk_source                                  │
└─────────────────────────────────────────────────────────────┘
```

三者职责不重叠：

| 关注点 | 归属 | 配置文件 |
| --- | --- | --- |
| 任务拆分、worktree 隔离 | Paseo | `~/.paseo/config.json` |
| 上下文压缩阈值 | pi | `~/.pi/agent/settings.json` |
| Desktop 能否打开 | 本仓库 | `scripts/desktop/` |

---

## 3. 工具清单

全部位于 `scripts/desktop/`，均已纳入版本控制。

### 3.1 `verdict.py` —— 判定内核

不单独运行，被其余脚本复用。核心是**用 Tableau 自己的日志判定**：

| 日志特征 | 判定 |
| --- | --- |
| `end-workspace.load-workbook` 且无错误对话框 | `LOADED` |
| 出现 `show-detailed-error-dialog` | `FAIL` |
| 超时未匹配到进程 | `UNKNOWN` |

`UNKNOWN` **一律当作失败**，重新验证后再下结论，绝不能当通过。

两个必须注意的实现细节：

- Tableau 启动时会把 `log.txt` 轮转成 `log_bk.txt`，所以「比较文件大小」
  的办法会漏掉新文件。正确做法是扫描**所有**日志中时间戳不早于启动时刻的行。
- Tableau 会把第二次启动**转发给已在运行的实例**。所以两次测试之间必须
  `kill()` 并等待进程退出，否则读到的是上一个进程的日志。

可通过环境变量覆盖：

| 变量 | 用途 |
| --- | --- |
| `TABLEAU_EXE` | 换用其他 Desktop 版本（默认 2026.2） |
| `TABLEAU_LOG_DIR` | 换用其他日志目录 |

日志目录自动探测中英文两种名称（`我的 Tableau 存储库\日志` 与
`My Tableau Repository\Logs`）。

### 3.2 `check.py` —— 单个工作簿

```bash
python scripts/desktop/check.py iterations/2020-03-07-ww10-spatial-buffers/outputs/replicated-workbook.twbx
```

退出码：`0` = LOADED，`1` = FAIL，`2` = UNKNOWN。

### 3.3 `check_batch.py` —— 多个工作簿

```bash
python scripts/desktop/check_batch.py path/a.twbx path/b.twbx
```

输出固定宽度，便于和基线 diff。

### 3.4 `verify_corpus.py` —— 回归基线（**最重要的门禁**）

打开基线清单里的每个案例并汇总。清单在
`scripts/desktop/desktop_baseline_cases.txt`，包含**50 个曾经打不开、现在
全部能打开**的案例。

```bash
python scripts/desktop/verify_corpus.py
python scripts/desktop/verify_corpus.py --json /tmp/result.json
```

退出码：全部 LOADED 才返回 `0`。**任何 SDK 或 builder 改动之后都应跑这个**，
确认没有把已修好的案例打回去。

### 3.5 `sdk_source.py` —— 报告/断言当前用的是哪个 SDK

```bash
python scripts/desktop/sdk_source.py
# origin       C:\...\cwtwb\src\cwtwb\__init__.py
# version      0.27.1
# git          a6ce15a
# selected_by  editable install
# sdk_root     C:\...\cwtwb\src

# 断言必须是某个 worktree，否则非零退出
python scripts/desktop/sdk_source.py --expect my-sdk-worktree
```

### 3.6 `build_and_check.py` —— 跨仓库闭环（**核心工具**）

重建案例 → 用 Desktop 验证，并**强制确认**实际导入的 SDK 就是指定的那个。

```bash
# 用当前 editable 安装的 cwtwb
python scripts/desktop/build_and_check.py iterations/2020-03-07-ww10-spatial-buffers

# 用某个 cwtwb worktree，且路径不符就报错退出
python scripts/desktop/build_and_check.py iterations/2020-03-07-ww10-spatial-buffers \
    --sdk-src C:/Users/imgwho/.paseo/worktrees/xxxx/my-sdk/src

# 批量（文件里每行一个 iteration 目录名）
python scripts/desktop/build_and_check.py --cases-file my_cases.txt --sdk-src .../src

# 只重建，不开 Tableau（快速迭代时用）
python scripts/desktop/build_and_check.py <case> --skip-desktop
```

它会打印实际生效的 SDK，并在 `--sdk-src` 与生效值不一致时**直接失败**。
这一步是为了防止「改了 SDK 但构建用的是旧代码」这种静默错误。

---

## 4. 跨仓库迭代 cwtwb：问题与解法

### 4.1 问题

`cwtwb` 是 editable 安装：

```
site-packages/_editable_impl_cwtwb.pth  →  <主检出>/cwtwb/src
```

这是**写死的单一路径**。实测：在 wow 的 worktree 里 `import cwtwb`，
解析到的仍是**主检出**的 cwtwb。

后果极其隐蔽——你在 cwtwb 的 worktree 里改了 SDK，在 wow 的 worktree 里
构建，构建成功、测试通过，但**根本没用到你的改动**。

### 4.2 解法

`PYTHONPATH` 的优先级高于 editable 路径（实测 `sys.path` 中位于其之前），
因此指向 SDK worktree 的 `src` 即可可靠覆盖。

`build_and_check.py --sdk-src` 和 `sdk_source.py` 已把这套逻辑封装好：

```
CWTWB_SRC 环境变量  >  PYTHONPATH 中的 cwtwb  >  环境默认的 editable 安装
```

优先级由 `sdk_source.resolve()` 实现，并有单测覆盖
（`tests/test_desktop_sdk_source.py`）。

### 4.3 完整闭环

```
1. cwtwb 开 worktree，改 SDK
       paseo workspace create --isolation worktree --mode branch-off \
         --new-branch fix-xxx --base origin/main     # 在 cwtwb 仓库里执行

2. wow 开 worktree（可选，改案例 builder 时需要）
       paseo workspace create --isolation worktree --mode branch-off \
         --new-branch fix-xxx-cases --base origin/main

3. 用 SDK worktree 重建并验证
       python scripts/desktop/build_and_check.py <case> --sdk-src <cwtwb-wt>/src

4. 跑回归基线
       python scripts/desktop/verify_corpus.py

5. 更新 requirements.txt 的 pin 到新 SDK commit
       cwtwb @ git+https://github.com/aidatacooper/cwtwb.git@<new-sha>

6. 双 PR：cwtwb PR + wow PR（含 pin 更新与重建产物）

7. 合并
```

第 5 步很关键：CI 按 `requirements.txt` 安装 SDK。pin 不更新的话，
CI 重建出的产物与提交的产物不一致。

---

## 5. 并行工作：worktree 隔离

Paseo 里是**两级结构**：`project`（注册的仓库根）→ `workspace`（检出）。

已注册的 project：

| project | 类型 | 能否 worktree 隔离 |
| --- | --- | --- |
| `wow-tableau-problem-solving` | git | ✅ |
| `cwtwb` | git | ✅ |
| `dbskill` | git | ✅ |
| `guagua_xhs` | git | ✅ |
| `project`（Desktop\project 本身） | non_git | ❌ |

**非 git 目录无法做 worktree 隔离**。如果需要，`git init` 后重新注册即可，
不要靠搬动文件夹来解决——搬动会打断已有的 git remote 关联和未合并分支。

命令示例：

```bash
# 新建隔离工作区
paseo workspace create --isolation worktree --mode branch-off \
  --new-branch feat-x --base origin/main --json

# 列出
paseo workspace ls

# 归档（会删除 worktree 目录，本地分支需另行清理）
paseo workspace archive <workspaceId>
```

> 注意：归档会删掉 worktree 目录，但**不会**删除本地 git 分支。
> 需要 `git branch -D <name>` 单独清理。

---

## 6. 委派给子 agent

### 6.1 已配置的 agent profiles

位于 `~/.paseo/config.json` → `daemon.agentProfiles`：

| Profile | 模型 | Thinking | 用途 |
| --- | --- | --- | --- |
| **Case batch fix** | deepseek-v4.1-flash | high | 长时批量修复 + 验证 |
| **Review & verify** | hy3 | high | 独立复核（故意换模型） |
| **Root cause & plan** | deepseek-v4.1-flash | max | 硬诊断/规划，只出方案 |
| **Docs & content** | hy4-preview-f | high | 文档、写作 |

每个 profile 的 `notes` 字段会被 orchestrator 通过 `list_profiles` 读取，
据此挑选。修改 notes 后执行 `paseo reload` 生效。

### 6.2 委派时的硬性要求

给子 agent 的任务提示里**必须**包含：

1. 使用哪个 SDK：`--sdk-src <cwtwb-wt>/src`，否则会静默用错 SDK
2. **必须**跑 Desktop 验证，`FAIL` / `UNKNOWN` 都不算通过
3. 完成后跑 `verify_corpus.py` 确认没有回归
4. 把进度写进仓库文档（本文件或审计文档），**不要只留在对话里**——
   这是防进程崩溃的关键

第 4 条最重要：长任务中 agent 可能因上下文过大而崩溃。写进磁盘的进度
对崩溃免疫，接手的人（或 agent）可以据此继续。

### 6.3 委派示例

```
用 Case batch fix 那个 profile，给这批案例开 worktree 隔离的工作区。

SDK 用 C:\Users\imgwho\.paseo\worktrees\<id>\<slug>\src
（必须用 --sdk-src 指定，并用 sdk_source.py 确认生效）

每个案例构建后必须跑 Desktop 验证，FAIL 和 UNKNOWN 都不算通过。
全部完成后跑 scripts/desktop/verify_corpus.py 确认 50 个基线案例无回归。

把每个案例的结果和发现的根因写进 docs/ 下的文档。
```

---

## 7. 上下文压缩配置

`~/.pi/agent/settings.json`：

```json
{
  "compaction": {
    "enabled": true,
    "reserveTokens": 16384,
    "keepRecentTokens": 20000,
    "modelOverrides": {
      "workbuddy-ai/deepseek-v4.1-flash": { "reserveTokens": 400000 }
    }
  }
}
```

触发条件：`contextTokens > contextWindow - reserveTokens`。

对 1M 窗口的模型，默认 `reserveTokens` 只有 16384，意味着**要到 98 万才压缩**
——实践中等于不压缩，直到进程先崩溃。设成 400000 后，60 万就压缩。

`modelOverrides` 的 key 必须是精确的 `provider/modelId`（区分大小写）。
`reserveTokens` 同时影响摘要请求的输出上限，不要设得过分离谱。

手动压缩：`/compact`，可带指令如 `/compact 保留 XSD 修复的细节`。

---

## 8. 验收门禁清单

一次改动合入前应全部满足：

- [ ] `python -m unittest discover -s tests` 通过
- [ ] `python scripts/validate_iteration.py <case>` 通过（XSD 门禁）
- [ ] `python scripts/desktop/build_and_check.py <case> --sdk-src <wt>/src` 返回 LOADED
- [ ] `python scripts/desktop/verify_corpus.py` 返回 `LOADED=50 FAIL=0 UNKNOWN=0`
- [ ] 若 SDK 有改动：`requirements.txt` 的 pin 已更新到新 commit
- [ ] 若产物被重建：`evidence/cloud-verification.json` 的 hash 需通过采集流程刷新
- [ ] 进度与根因已写入 `docs/`

---

## 9. 已知限制

1. **Desktop 验证依赖本机**。需要安装有授权的 Tableau Desktop 2026.2，
   且是 Windows（脚本用了 `powershell` / `tasklist`）。CI 上跑不了，
   因此目前是**人工门禁**。若要自动化，需要一个装有 Desktop 的专用 runner。

2. **每次验证约 10–60 秒**。实测一个 LOADED 案例约 11 秒（含 kill、等待
   进程退出、加载判定）。出现 `UNKNOWN` 会触发重试，耗时会明显增加。
   50 个案例全量约 10–30 分钟。

3. **`2020-06-12-ww24-moving-average-trend`** 的 verifier 对
   table-calc `ordering-field` 的断言较宽松（接受两种形式）。见
   `docs/generated-twbx-desktop-load-audit.md` 第 8.2 节。

4. **4 个 historical 案例**（schema 1.0.0）按仓库策略只读，未纳入基线。

---

## 10. 相关文档

- `docs/desktop-log-verdict.md` —— 判定原理（为何读日志而非看界面）、
  三类结果（LOADED / FAIL / UNKNOWN）的实测样本、误报源、判定伪代码
- `docs/generated-twbx-desktop-load-audit.md` —— 51 个产物为何打不开、
  50 个案例的逐个修复记录与根因（manifest 标志配对表）
- `scripts/validate_iteration.py` —— XSD 门禁实现
- `tests/test_desktop_sdk_source.py` —— SDK 选择逻辑的单元测试
- `scripts/desktop/desktop_baseline_cases.txt` —— 50 个回归基线案例
