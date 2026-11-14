# 开始解一个 case

先读 `AGENTS.md`；长任务另读 `docs/long-running-tasks.md` 的进度与大文件规则。
并行分工以 `docs/cross-repo-desktop-workflow.md` 为准，不要求特定模型或 profile。

## 1. 准备与身份

```bash
python -m pip install -r requirements.txt
python scripts/case_intake.py "<文章URL>"
python -m unittest discover -s tests
```

requirements 的 pin 是可复现依赖，不等于最新 PyPI stable。按
[SDK 迭代流程](iterating-cwtwb-and-wow.md) 查询并记录 stable、prerelease、
main，显式选择本次 SDK。`posts/`、`dashboards/`、`dataset/` 是 gitignore
生成物；缺素材时运行 `python download_all.py --refresh`。

默认以 PyPI stable 建立诊断基线；任务明确指定源码基线时，可用 requirements
中的完整 Git SHA 安装并记录 source 渠道、版本、导入路径及实际 SHA。
当前 pin 是已合并的 `0.29.0a4` 源码，PyPI 发布仍待完成；安装该 pin
不等于安装 PyPI a4，也不能记作已跑 stable 基线。

检查已有 case issue，避免重复认领。按任务授权新建临时分支，不直接提交 main，
不覆盖他人未提交改动。普通 case PR 只改本 case 和生成索引；SDK 修复另提 PR。
仓库约定优先 `--merge`。Squash 会产生新 SHA，但不必然使旧提交不可达；
依赖 pin 必须指向合并后可获取的上游提交。

```bash
python scripts/prepare_case.py \
  --workbook-url "https://public.tableau.com/views/WORKBOOK/VIEW" \
  --iteration-id YYYY-MM-DD-wwNN-short-slug \
  --challenge-year YYYY \
  --case-id wow-YYYY-wwNN-short-slug \
  --post-url "<文章URL>"
```

身份采用 intake 结果，不从文章年份猜挑战年份。只有官方日期已核实时才传
`--challenge-date` / `--challenge-url`。prepare 会抽取数据并写
`inputs/source-lock.json`，不把作者工作簿放入 iteration。

## 2. 执行与验收

| 步骤 | 动作与产出 |
| --- | --- |
| 分析 | 读文章、作者工作簿和参考图，写 `analysis.md`；列出全部业务要求及可观察的 acceptance IDs，包括交互。 |
| 基线 | 修改 SDK 前，默认用最新 PyPI stable，或任务明确指定的源码 SHA，构建、验证并保存真实证据；标明渠道，builder 只用公共 SDK 和允许的数据输入。 |
| 定位 | 用独立环境/检出测试 prerelease、fresh main；逐次追加 `cwtwb.runs`，不能覆盖 stable 失败。 |
| 修复 | case 用法错误改 builder；可复用 SDK 缺口走独立 synthetic 测试与 SDK PR，维护 gap 生命周期。 |
| 重建 | 用最终选定 SDK 跑 validator、builder、verifier；SDK 改动还需重建回归清单。 |
| Desktop | 独占 Desktop，所有目标必须 LOADED；FAIL、UNKNOWN、NOBUILD 都不通过。 |
| 行为 | 对最终产物逐项验证交互、数值和预期状态；XML 存在、能打开都不能替代交互验证。 |
| 冻结证据 | 所有重建完成后采集 Cloud/交互/截图证据并绑定最终产物 hash；重建后必须重采。 |
| 收尾 | 更新真实状态、remaining_work、gap、索引及进度，提交 PR；只有完整验收通过才称 case solved。 |

`cwtwb.runs` 每次包含实际版本、result 和独立 evidence 文件；该文件记录日期、
来源渠道、导入路径、完整 SHA/dirty 状态（包安装则记录版本及包 hash）、
命令、产物 hash、各 acceptance ID 结果。最新 run 与 `tested_version`、
`cwtwb_result` 一致。不要照抄模板里的旧版本或先写尚未执行的通过结果。

复用缺口记录 ID、负责人、最小复现、受影响 acceptance IDs、下一步及生命周期：
`identified -> reproduced -> fixing -> upstream merged -> case retested -> accepted`。
实际创建 issue 后才填 `related_cwtwb_issues`，实际创建 PR 后才在 gap 记录关联 URL；
未创建就明确写“未创建”，不能编造链接或将计划写成已完成。

## 3. 门禁与完成条件

按 [跨仓库流程](cross-repo-desktop-workflow.md) 先设置 SDK 环境，再执行：

```bash
python scripts/validate_iteration.py iterations/<id>
python -m unittest discover -s tests
python scripts/desktop/build_and_check.py iterations/<id> --sdk-src <selected-sdk>/src
python scripts/desktop/verify_corpus.py
```

validator 和 build_and_check 会重建；`verify_corpus.py` 只打开已有产物。
回归数量取 `scripts/desktop/desktop_baseline_cases.txt`，不硬编码数量。
完成构建和 Desktop 后，再运行该 case 的交互/Cloud 采集流程、复核最终证据，
最后运行 `python scripts/case_catalogue.py --write` 更新索引。

`functional_status`、`visual_status`、`cwtwb_result` 分别如实记录。
未验证的交互保持 pending/remaining_work，不能因 XML 检查通过而标 replicated。
partial/blocked PR 可以保存可复现进展，但合并不代表解题完成；保持后续任务和
gap 打开，直到最终 SDK pin 下全部必需 acceptance 场景通过。

Desktop 需要本机 Windows 与可用授权；记录实际 Tableau 版本。
缺作者文件、授权或验证环境时记录 blocker，不把无法执行的门禁写成通过。

相关说明：`docs/desktop-log-verdict.md`、
`docs/protocols/community-case-contribution-v1.md`、
`docs/protocols/case-identity-and-naming.md`。
