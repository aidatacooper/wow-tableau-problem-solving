# 2026 WW06：Null 安全平均与 Apply

日期：2026-07-30  
状态：replicated
case_id：`donna-2026-02-15-44019b20eed6`  
workbook_id：`tableau-f9dff954fb215221`

## 1. 问题理解

普通日期 quick filter 会在计算前删除没有订单的层级和 weekday 组合，因此 `ZN`
无法把不存在的 mark 变为 0，Average 也只会除以有订单的组合。正确链条需要参数
日期范围保留数据域、`INDEX()` 触发域补全、`ZN(COUNTD(...))` 转为 0，再使用
Average subtotal。日期范围先在 Apply worksheet 选择，再由参数动作提交。

## 2. Tableau 解题链

```text
Category > Sub-Category > Manufacturer hierarchy
→ weekday columns
→ pMinDate / pMaxDate
→ #Orders in Date Range
→ INDEX on Detail
→ missing marks densified
→ ZN converts null to 0
→ Average subtotals

Apply worksheet context date filter
→ Min Date / Max Date
→ Set Min Date + Set Max Date parameter actions
→ table recalculates only after Apply
```

## 3. cwtwb 实现

`build_replication.py` 使用原 TWBX 的 Manufacturer 数据源与 Hyper extract，但清空并
独立重建全部 worksheet、Dashboard 和 actions：

- Null-safe Square table；
- Category、Sub-Category、Manufacturer 和 weekday 布局；
- INDEX domain completion；
- Average subtotals；
- Apply worksheet 和 context date filter；
- 两条原生参数动作；
- 独立 TWB/TWBX。

本案例发现 `clear_worksheets()` 会保留引用已删除视图的旧 actions，导致新参数
动作进入非法 XML 顺序。cwtwb `18d9361` 已同步清理悬空 actions，并增加回归测试。

首次云端发布还发现裸日期字段的 bounded quantitative filter 被错误绑定为
`MONTH(Order Date)`。cwtwb `cd98ce8` 现在将这类过滤器绑定为连续 Exact Date，
并增加回归测试。

## 4. 差异

- 未逐像素复刻色板、边框、banding、字体和 padding；
- 未加入只负责取消 Apply 选中状态的辅助 filter action；
- 显示两个日期参数控件作为 Apply 交互的补充；
- 必要的零值、域补全、Average 和双参数 Apply 语义均已保留。

## 5. 验证

- 本地 XML、TWBX 包结构、Hyper 打包、round-trip：通过；
- 确定性案例验收：通过；
- analyzer：识别 Parameter Action、Domain Completion、Hierarchy、Subtotal 等；
- cwtwb 全量回归：317 passed，25 skipped；
- TWB-only Cloud endpoint：三次未成功，最终返回 HTTP 400；
- 首次 TWBX 上传：Tableau Cloud 拒绝 `MONTH(Order Date)` 日期范围过滤器；
- 修复后 TWBX 发布与可打开性验证：通过，服务端识别 2 个 worksheets 和
  Dashboard，workbook_id 为 `ea73a5a8-b104-4602-a5b4-3589ef4a588d`。

## 6. 当前状态

```text
status: consumed
replication_status: replicated
```

原始 Hyper 数据、完整解题链、本地验收、回归测试和 Tableau Cloud 可打开性验证
均已通过。
