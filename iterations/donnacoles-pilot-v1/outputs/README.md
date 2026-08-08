# cwtwb Donna 案例能力演示

生成文件：`dynamic-moving-average-and-parameter-action.twbx`

## 业务问题

管理者希望查看销售额趋势，但单月波动很大。同时，他需要：

1. 自己决定移动平均窗口，例如 3 个月或 6 个月；
2. 点击一个产品类别后，趋势图立即切换到该类别；
3. 清除选择后回到全部类别。

## Tableau 交互

- 左侧条形图：选择 `Furniture`、`Office Supplies` 或 `Technology`。
- 左下角参数控件：修改 `Moving Average Window`。
- 右侧折线图：显示所选类别、所选窗口下的动态移动平均。
- 清除条形图选择：`Selected Category` 参数恢复为 `All`。

## 本例验证的 cwtwb 能力

- 计算字段可以声明真实的 `<table-calc ordering-type="Rows">`。
- 表计算元数据会传播到 worksheet 的 `column-instance`。
- Dashboard 可以生成原生 `<edit-parameter-action>`。
- TWBX 自动打包示例 Excel 数据源，可以作为独立案例交付。

## 重新生成

在项目根目录运行：

```powershell
$env:PYTHONPATH='src'
python examples/donna_pilot_showcase.py
```

## 案例 C：空值组合也参与平均值

生成文件：`null-safe-average-with-domain-completion.twbx`

这个案例解决“某个分类在某个工作日没有订单时，普通视图会直接省略该组合，
导致平均值只除以有数据的天数”的问题。实现由三个独立语义组成：

1. `Location Hierarchy` 写入 Tableau datasource drill path；
2. `INDEX()` 作为 Detail 表计算触发 domain completion，让缺失组合生成 marks；
3. `#Orders = ZN(COUNTD([Order ID]))` 把补出的空 mark 变成 0，并将小计方式设为
   `Average`、标签设为 `Avg.`。

在 Tableau 中打开后，`Null-safe Average` 工作表按 Category、Sub-Category 和
weekday 展示订单数；其平均小计会把没有订单的 weekday 按 0 纳入，而不是忽略。

重新生成：

```powershell
$env:PYTHONPATH='src'
python examples/donna_case_c_showcase.py
```
