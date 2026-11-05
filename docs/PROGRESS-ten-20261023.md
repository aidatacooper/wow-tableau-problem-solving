# 进度：2026-10-23 再解决 10 个 WoW case

> **最终状态（2026-10-24）**：10/10 已验收并集成本地协调分支；121 已解、228 未解。全部 Desktop LOADED、Cloud 数据 PASS、冻结 XSD/metadata/hash PASS，83 tests OK。下方为追加式历史记录，早期 pending 不代表当前状态。详见 [最终结果](TEN-CASE-RESULTS-20261024.md)。

- 基线：main d52ecab；111 个 replicated case。旧 unsolved-posts.md 的 259 和 batch-17 的 237 均为过时或目录计数。
- 本地归档：349 篇文章（2026-10-09 抓取）；按 URL 加历史文章路径匹配后，238 篇尚未解决，其中 233 篇带工作簿链接，5 篇无链接。
- SDK：固定 `.sdk-pins/cwtwb-23b1df0/src`；系统 editable 指向已删除目录。本次进程显式设置 PYTHONPATH，不改全局安装。
- Python：`C:/Users/imgwho/AppData/Local/Python/pythoncore-3.14-64/python.exe`，已确认 yaml / cwtwb / tableauhyperapi 可导入。
- 主协调分支：`chore/wow-ten-20261023`；保留用户已有的 `docs/PROGRESS-daily-watch.md` 改动。
- 每个 case 独立分支、独立 worktree。Desktop gate 统一串行执行；无 LOADED 证据不计入完成。

## 工作清单

- [ ] 01 2021-07-23 Olympic Schedule — feat/2021-ww29-olympic-schedule；Paseo c932eacb-4620-41d2-9575-7941bc7e847a
- [ ] 02 2021-07-29 Streaking — feat/2021-ww30-streaking；Paseo 9338f57d-464a-40f6-af74-a01a13a742f0
- [ ] 03 2021-08-05 Needle in Haystack — feat/2021-ww31-needle-haystack；Paseo 07a9a8a0-2e95-4e80-a9a0-79ef7d678b21
- [ ] 04 2021-08-12 Survey Data
- [ ] 05 2021-08-29 Moving Average
- [ ] 06 2021-08-31 Consecutive Starts
- [ ] 07 2021-09-02 Change
- [ ] 08 2021-09-12 Extract Runs
- [ ] 09 2021-09-23 Net Change
- [ ] 10 2021-10-08 Stacked Bars

## 恢复后的验收记录
- 2026-10-23：前四例 frozen artifact Desktop 均 LOADED（各 case evidence/desktop-verification.json）；corpus 已完成 50/0/0，不重复跑。
- Survey 最终 SHA d5215ce32188afbc573240a57cce7572a05ebb43522b768acea90d6c88bc53f8，隔离构建/XSD PASS、15 CSV / 339 checks PASS、83 tests OK；已填 verified/replicated/workaround。待独立视觉复核及提交。
- Needle 最新 Cloud capture 成功，待检查 CSV 和记录新 hash。
- Streaking 再次 Cloud 空白，根因包括嵌套 table-calc ordering-field 仍引用不存在的 Order Date Month 名称，以及 Legend 轴不在 shelf；协调者已修 builder，正在重采。继续 partial。
- Olympic 原作者只公开 dashboard，CSV 请求不存在的 Date Chart 失败；将用原始作者图 + replica CSV/oracle，禁止改写作者。
- 第二批：ww33 agent e8adee31-1bc9-435f-8cea-5da05ff4c581 已完成本地 e5e735b；ww34 e66d3137-26ef-4ed5-a728-d9130e7bbea7、ww35 7cb37b75-a926-4305-ad88-bb7b1b886729 运行中。

## 已完成步骤

- [x] 盘点索引、历史进度与 git 状态；修正以目录数代替已完成案例数的计数方法。
- [x] 验证有依赖的 Python 与固定 SDK 可导入。
- [x] 首批三个 case 已分派至独立工作区；要求 builder 不读取作者工作簿。

## 下一步

基线83 tests和Desktop corpus50/0/0已完成；以文末最新验收记录为准，不重跑已冻结产物。

## 阻塞

暂无案例级阻塞；默认沙盒无法访问系统 Python，验证命令使用已授权的提权执行。

- [x] 固定 SDK 基线：83 tests OK（16.759s）；日志 scratch/ten-20261023-unit.log。
- [ ] Desktop corpus 尚未启动：自动审查要求先核实进程和互斥锁，正在只读检查。

- [x] 04 Survey Data：独立 builder 已生成工作簿；verifier PASS（63 respondents / 1134 rows / 19 filter states / 8 filter actions）。工作区 ../wow-ten-20261023-survey。
- [ ] Cloud 上传被自动审批两次拒绝（要求用户明确授权目标与 payload）；已发异步授权问题。只读核对证明配置站点与 100 个历史案例相符，但审查仍要求明确授权。所有 worker 已获通知暂停上传，本地工作继续。

- [x] 04 Survey Data：修正 size / stroke-color 属性后，validate_iteration 完整隔离构建 + verifier + XSD PASS。尚未 Desktop / Cloud。

- [x] Desktop baseline corpus 完成：LOADED=50 FAIL=0 UNKNOWN=0 NOBUILD=0；证据 scratch/ten-20261023-corpus.json。
- [x] 后六个 intake 已保存 scratch/ten-intake-YYYY-MM-DD.json；正式周次 33 / 34 / 35 / 36 / 38 / 40。

- [x] 用户明确授权本批 10 个案例原作者/复现文件上传现有 Cloud 验证站点。
- [x] 04 Survey Data Desktop check：try1 LOADED。
- [ ] Cloud 会话并发互相失效（发布成功后读取视图 401）；已通知各 worker 停止发起 Cloud，改由主协调者串行。原作者隐藏工作表不修改，仅作整图比较；replica 完整 CSV 对独立 oracle。

## 2026-10-24 最新恢复点

- 基线严格 verified/historical 口径重新计算仍是111已解/238未解，233带链接。
- WW29/30/31/32/33已通过最终冻结产物Desktop、Cloud CSV与隔离重建；不同模型独立复核进行中。
- WW35最终SHA 5e57e91e7beaf45ac3f066f030a3ee5e918522791df1c3adab848871b59a683a，34类别年度精确数值PASS，Desktop LOADED，隔离重建/XSD/metadata PASS。已修自动stacking与当前年份前景绘制；Live author标签正常，早期标签错位仅归档图。
- WW34修复错误的多个ordering_field节点，改为一个table-calc的order children并给所有嵌套依赖设置地址；INDEX改continuous。最新Desktop LOADED，65040字段PASS，7680场全量oracle，原作者公开720场一致。由finish_ww40 agent补最终metadata/commit。
- WW36处理条厚度、Key、参考带字段、标题已修，冻结SHA 62a3a5e0eb59bdac88e305254ca10e0d7bbf8057bd3a47838e3351beb6a76b55。209640数值oracle校验器已写，正重采Cloud绑定。
- WW38本地d3502f4，root已通过public API解除replica隐藏以导出CSV，正在重采三states；作者工作簿保持不变。finish_ww38 agent写Cloud校验。
- WW40本地0cb79a7，Desktop LOADED；原作者只公开dashboard，删除不可达Chart请求，正在采三states截图及replicaCSV。
- Paseo batch provider429；case9/10由当前模型子代理接续完成，没有重复从头做。
- 全局Cloud和Desktop各自锁保护；禁止在验收后运行会原地重build的validate_iteration，使用run_case_scripts_isolated。
- 接下来：完成后三例，多模型复核，分别提交10case最终证据，集成协调分支并刷新catalogue/backlog。保留用户daily-watch修改。

- Final GPT review resolved: WW36 visible wait threshold/status headings added; final artifact e8694891dbe75cd3fb029affcb74c1c5b1856400c716d1e44153728418357cbd passed Desktop LOADED, all3Cloudstates and209640 numericchecks again. Final audit table refreshed. WW35 omittedheaders disclosed. All10complete.
