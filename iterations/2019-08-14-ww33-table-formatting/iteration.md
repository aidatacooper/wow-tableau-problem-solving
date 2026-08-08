# 2019-08-14 WW33：Table Formatting

状态：completed  
case_id：`donna-2019-08-14-9a4c743596c1`

## 目标

从空白 Workbook 使用 cwtwb SDK 重建作者案例的核心表格语义：区域销售占比、利润率、数量/销售/利润标签、高亮阈值，以及对应的 Bar/Table/Dashboard 结构。

作者 TWBX 只用于分析和来源锁定；构建阶段只允许使用 replication spec、空白模板和从作者包中提取的 Hyper 数据。

## 验收

- 构建脚本不读取作者 TWB/TWBX；
- TWB/TWBX 可由 cwtwb SDK 生成并通过本地结构验证；
- 参数、计算字段、worksheet、dashboard 和 Hyper 依赖存在；
- 使用 `.env` 进行 Cloud/API 验证；
- 保存原版与当前看板截图并做视觉对比。

## 结果

- `replication_status: visually_replicated`；
- 从空白模板构建，构建过程没有读取作者 TWB/TWBX；
- 本地 TWB/TWBX 结构与 Tableau semantic validation 通过；
- Tableau Cloud 上传和截图通过；
- 原始 PNG 为加载占位图，不能用于像素级比较，已在 `evidence/cloud-validation.json` 记录。
