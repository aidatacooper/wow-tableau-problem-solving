# Problem model

用户要在 Region 与 Sub-Category 交叉表中比较选定区域和其他区域的销售表现，同时显示 Sales、Quantity、Profit Ratio，并通过阈值高亮行。难点是选定区域的分母必须保持在 Year + Sub-Category 粒度，不能因当前 Region 过滤而改变；高亮还要驱动粗体与普通标签的互斥显示。

必要语义：参数阈值、FIXED 粒度的总销售、选定区域销售百分比、其他区域百分比、Highlight 布尔值、利润率、双标签字段和表格布局。

可替代内容：精确字体、颜色、padding、作者署名和装饰性标题。
