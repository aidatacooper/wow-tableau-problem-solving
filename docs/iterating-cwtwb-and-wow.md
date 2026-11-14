# 迭代 cwtwb 和 WoW

- SDK：`C:/Users/imgwho/Desktop/project/cwtwb`
- cases：`C:/Users/imgwho/Desktop/project/wow-tableau-problem-solving`

目标是补齐可复用能力并完成整题验收。partial/blocked PR 合并只保存进度；
SDK PR 合并也只完成上游修复，仍需 case 重测与验收。

## 1. 明确“最新”与实际测试来源

三条渠道不能混写：

| 渠道 | 查询与记录 |
| --- | --- |
| PyPI stable | 查 PyPI 非预发布、非 yanked 的最新发行，记录版本和下载包 hash。 |
| PyPI prerelease | 单独查 alpha/beta/rc 是否已发布；记录确切版本，不把 main 的版本号当作已发布包。 |
| Git main | fetch 上游 main，记录远端、完整 SHA、该提交版本及查询时间；不把本地旧 main 当最新。 |

发布快照（2026-11-14）：`cwtwb` PR #24 已合并，
合并提交 `1d578a3f815dde189860d0243404bf84057a19f8` 是本仓库 requirements pin。
公开 tag `v0.29.0a3` 指向该提交；PyPI `0.29.0a3` 的 wheel 和 sdist 已公开，
SHA256 与本地已检查发布包一致。这是 prerelease，不是 stable。
这是带日期的发布记录，不是后续运行的固定期望；每次任务重新查询三个渠道。

修改 SDK 前先用 stable 建立失败基线，再测试可用 prerelease/main。
使用分开的环境/检出，避免安装覆盖或 editable 路径串用。记录实际 import 路径、
版本、完整 SHA 和 dirty 状态；源码有未提交修改时，另存 diff，不能只报 HEAD。
包安装没有 Git SHA 时写“不适用”，保存确切包来源与 hash。

显式选择与所有命令的环境设置见
[跨仓库 Desktop 流程](cross-repo-desktop-workflow.md)。每次真实运行追加
`cwtwb.runs` 的 version/result/evidence；证据文件保存来源与命令，保留先前失败。
`tested_version`、`cwtwb_result` 与最新 run 对齐。

## 2. 从缺口到上游修复

| 问题 | 处理 |
| --- | --- |
| 现有 API 用错 | 修 case builder 或使用说明 |
| 现有 API bug | synthetic 复现 + SDK bug 修复 |
| 可复用 primitive 缺失 | 通用 SDK API + synthetic 回归测试 |
| 单题视觉差异 | 记录差异；workaround 仍须遵守公共 SDK 边界 |

在 analysis/进度文档维护 gap ID、负责人、失败 acceptance IDs、最小复现、
下一步与状态：
`identified -> reproduced -> fixing -> upstream merged -> case retested -> accepted`。
实际创建后才关联上游 issue/PR URL；issue 写入 `related_cwtwb_issues`，
PR 写入 gap 记录。没有创建时写“未创建”，不要虚构关联。

SDK 测试不依赖作者工作簿或作者数据。先建立失败测试，再修改通用实现；
覆盖适用的 builder -> dispatcher -> public Python facade -> MCP tool ->
capability registry 路径，验证公共入口、参数转发与注册一致，并加 XML/XPath
回归测试。结构测试不能证明 Desktop 交互可用；还需 case 端行为证据。
按 SDK 仓库自己的 AGENTS 与开发依赖运行相关测试及要求的检查。

## 3. 集成、冻结证据、完整验收

1. 本地可以先用 SDK 修复检出验证 case，无须等待上游合并才测试。
2. SDK PR 通过检查并合并后，取得可获取的上游完整 SHA。
   WoW 的最终 `requirements.txt` pin 使用此 SHA，并验证新环境可安装。
   按仓库约定优先 merge；squash 产生新 SHA，不保证原 SHA 消失或长期可获取。
3. 用最终 pin 的源码重建 case 和 SDK 回归基线，验证 Desktop、业务数据和
   所有必需交互；将实际结果追加为新 run。
4. 所有重建完成后采集 Cloud/交互证据并绑定产物 hash。后来又重建则重采，
   不手改 hash 来冒充重新验证。Cloud 凭证见
   [凭证说明](tableau-cloud-credentials.md)，不得提交 token。
5. 更新 case 状态、gap、进度与生成索引。整题 acceptance 全通过才标 replicated；
   未验证/失败项仍写 remaining_work，partial PR 合并不能关闭未完成的整题任务。

## 4. 长任务与分工

每完成一个可验证步骤，更新 `docs/PROGRESS-<topic>.md`：
来源/SHA、实际结果、真实 issue/PR、阻塞、负责人及下一条可执行动作。
恢复时读进度与 git 状态；大文件只做定向搜索或摘要，见 `long-running-tasks.md`。

仅在任务授权且工具支持时委派。按文件/case 划分唯一写入责任人；
SDK 公共实现由单一负责人集成，pin、索引及最终状态由集成人统一更新。
共享 checkout 不并发编辑同一文件；独立检出也不能隔离 Desktop 进程和日志，
所有 Desktop 检查与交互采集排队串行。没有可用 agent 工具时按相同步骤顺序执行，
不依赖特定 profile、模型、定时巡检或上下文扩展已安装。
