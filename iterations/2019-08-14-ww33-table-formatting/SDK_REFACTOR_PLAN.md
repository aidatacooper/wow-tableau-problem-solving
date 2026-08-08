# WW33 Table Formatting — SDK 重构方案

> **文件**：`build_replication.py`（2091 行）→ 目标重构后约 350 行  
> **原则**：保持 `cwtwb` SDK 的通用性，新增 API 应对其他工作簿同样适用。  
> **状态**：设计方案，待实现。

---

## 一、现状诊断

### 1.1 脚本中各模块的代码量和性质

| 区域 | 行数 | 性质 | 是否可 SDK 化 |
|------|------|------|--------------|
| 常量定义（计算字段、字段名等） | ~200 | 业务配置，应保留在脚本 | ❌ 无需 SDK 化 |
| XML 辅助工具函数（`_el`, `_fmt`, `_dep_column` 等） | ~170 | 通用 XML 操作模式 | ✅ 完全吸收进 SDK 内部 |
| `build_title_worksheet` — 动态格式化标题构建 | ~130 | 富文本标题含字段引用 | ✅ 扩展现有 `set_worksheet_title` |
| `build_table_worksheet` — 10 列多 Pane 表格 | ~470 | 复杂多轴表格结构 | ✅ 新增 `configure_multi_column_table` |
| `build_bar_worksheet` — 折叠双轴 100% Bar | ~270 | 双轴 + 折叠轴 + Measure Names 编码 | ✅ 扩展现有 `configure_dual_axis` |
| `add_datasource_palettes` — 数据源调色板 | ~100 | 颜色映射注册 | ✅ 新增 `set_datasource_color_palette` |
| `add_shared_views` — 全局筛选器 | ~120 | 工作簿级别共享筛选 | ✅ 新增 `add_shared_filter` |
| `build_dashboard` — 固定尺寸仪表板布局 | ~150 | dashboard zone 树 | ✅ 现有 `add_dashboard` 已支持大部分，需补充细节 |
| `build()` 主流程 | ~160 | 编排逻辑，应保留 | ❌ 无需 SDK 化 |

### 1.2 目前 SDK 已支持的能力（无需新增）

- ✅ `editor.add_parameter()` — 参数
- ✅ `editor.add_calculated_field()` — 计算字段
- ✅ `editor.add_worksheet()` — 添加空工作表
- ✅ `editor.set_worksheet_hidden()` — 隐藏工作表 Tab
- ✅ `editor.add_dashboard()` — 仪表板（含 layout dict）
- ✅ `editor.configure_worksheet_style()` — 工作表样式
- ✅ `editor.configure_dual_axis()` — 双轴图（基础支持）
- ✅ Dashboard layout dict 中支持 `filter`、`paramctrl`、`text` 类型 zone
- ✅ `editor.set_hyper_connection()` — 连接 hyper

---

## 二、需要新增的 SDK 功能

共 **5 个新功能区域**，按实现优先级排序。

---

### Feature 1：工作簿级别共享筛选器 `add_shared_filter`

**对应脚本代码**：`add_shared_views()`（第 1638–1754 行，~120 行 XML）

**问题**：工作簿级别的"应用到所有工作表"筛选器目前无 SDK 支持，需手动拼接 `<shared-views>` 节点。

#### 新增接口

```python
# src/cwtwb/twb_editor.py (ParametersMixin 或新增 FiltersMixin)

def add_shared_filter(
    self,
    field: str,                          # 字段名，如 "Region" 或 "Order Date"
    values: Optional[list[str]] = None,  # 包含的成员值，如 ["East"]
    all_members: bool = False,           # 是否选全部成员（Sub-Category 情形）
    year: Optional[int] = None,          # 年份筛选快捷方式（YEAR 截断）
    view_name: Optional[str] = None,     # shared-view name，默认取数据源名
) -> str:
    """添加工作簿级别共享筛选器（应用到所有工作表）。

    每次调用追加一个 <filter> 到 <shared-view> 中。
    多次调用同一 view_name 的筛选器会合并到同一个 <shared-view>。
    """
```

**实现要点**：

1. 在 `editor.root` 下查找或创建 `<shared-views><shared-view name="ds_name">` 节点。
2. 在 `<shared-view>` 内写入 `<datasources>`、`<datasource-dependencies>`（包含所涉及字段的 `<column>` 和 `<column-instance>`，通过 `field_registry` 自动解析，无需手动构造）。
3. 追加 `<filter class="categorical">` + `<groupfilter>` 节点，支持三种模式：
   - `values` 列表 → `function="member"` + `member="..."`
   - `all_members=True` → `function="level-members"` + `ui:ui-enumeration="all"`
   - `year=N` → `function="member"` + `member="2018"`（整数值）
4. `<shared-views>` 插入位置：在 `<worksheets>` 之前。
5. Tableau XML namespace for UI attrs：`{http://www.tableausoftware.com/xml/user}`。

**重构后的脚本调用（~5 行替换 120 行）**：

```python
editor.add_shared_filter("Region", values=["East"])
editor.add_shared_filter("Sub-Category", all_members=True)
editor.add_shared_filter("Order Date", year=2018)
```

---

### Feature 2：数据源级别调色板 `set_datasource_color_palette`

**对应脚本代码**：`add_datasource_palettes()`（第 1536–1634 行，~100 行 XML）

**问题**：在 `<datasource><style>` 上注册调色板目前无 SDK 支持。颜色映射对某个字段的 `column-instance` 绑定是数据源级别语义，Tableau 的着色只有在这里声明才能正确解析。

#### 新增接口

```python
# src/cwtwb/twb_editor.py

def set_datasource_color_palette(
    self,
    field: str,                        # 字段名，如 "Highlight" 或 ":Measure Names"
    color_map: dict[str, str],         # {bucket_value: hex_color}
    is_measure_names: bool = False,    # True 时 field 写 "[:Measure Names]"，bucket 用引号包裹
) -> str:
    """在 <datasource><style> 上注册字段的调色板映射。

    Args:
        field: 字段名（通过 field_registry 解析为 column-instance name）。
        color_map: bucket 值到颜色的映射。
            - is_measure_names=False：bucket 值为直接字符串（如 "true"/"false"）
            - is_measure_names=True：bucket 值为完整的 "[ds].[instance_name]" 引用
        is_measure_names: 为 True 时使用 [:Measure Names] 作为 field 属性，
                          bucket 值写带引号字符串形式。
    """
```

**实现要点**：

1. 确保对应字段的 `<column-instance>` 在 `<datasource>` 直接子节点下存在（`column-instance` 插入位置须在 `column` 之后，遵守 Tableau content model 顺序）。
2. 在 `<datasource><style>` 节点下找或创建 `<style-rule element="mark">`。
3. 写入 `<encoding attr="color" field="..." type="palette">` + 各 `<map to="color"><bucket>value</bucket></map>`。
4. 布尔型字段 bucket 值写为裸 token（`true`/`false`，不带引号）；Measure Names bucket 值写为带引号字符串（`"[ds_name].[inst_name]"`）。

**重构后的脚本调用（~12 行替换 100 行）**：

```python
# Measure Names 控制 Bar 颜色
editor.set_datasource_color_palette(
    field="Measure Names",
    color_map={
        f'"[{ds_name}].{inst(N_PCT_SEL, "qk")}"': "#5c6068",
        f'"[{ds_name}].{inst(N_BAR_MIN1, "qk")}"': "#ffffff",
    },
    is_measure_names=True,
)
# Highlight 布尔字段控制 Table 行颜色
editor.set_datasource_color_palette(
    field="Highlight",
    color_map={"true": "#d3d3d3", "false": "#ffffff"},
)
```

---

### Feature 3：动态格式化标题 `set_worksheet_rich_title`

**对应脚本代码**：`build_title_worksheet()` 前半段（第 573–611 行，~40 行 XML）

**问题**：现有 `set_worksheet_title()` 只支持单纯文本 run，无法支持：
- 多段 run，每段有不同的字体大小 / 颜色 / 加粗
- run 中嵌入 Tableau 字段引用（`<[ds].[instance_name]>`，Tableau 会将其渲染为动态值）

#### 新增接口

```python
# src/cwtwb/twb_editor.py

def set_worksheet_rich_title(
    self,
    worksheet_name: str,
    runs: list[dict],
) -> str:
    """设置工作表的富文本动态标题（layout-options > title > formatted-text）。

    Args:
        runs: 格式化文本 run 列表，每个 run 是一个 dict，支持键：
            - "text" (str): 文本内容，可含形如 "<Field Name>" 的字段引用占位符，
                            SDK 自动解析为 "<[ds_name].[instance_name]>" CDATA。
            - "bold" (bool, optional): 加粗。
            - "fontsize" (str | int, optional): 字体大小。
            - "fontcolor" (str, optional): 十六进制颜色，如 "#666666"。
    """
```

**实现要点**：

1. 找或创建 `<layout-options><title><formatted-text>`，清空已有内容。
2. 对每个 run dict 创建 `<run>` 节点，按键设置属性（`bold="true"` / `fontsize="14"` / `fontcolor="#..."`）。
3. 对 `text` 值中形如 `<Field Name>` 或 `<[Parameters].[Param Name]>` 的模式，通过 `field_registry.parse_expression()` 解析并替换为 `<[ds_name].[instance_name]>` 格式，以 `etree.CDATA()` 包裹写入 `run.text`（Tableau 通过 CDATA 识别字段引用）。

**重构后的脚本调用（~8 行替换 40 行）**：

```python
editor.set_worksheet_rich_title("Title", runs=[
    {
        "text": "<Order Date> <Region> Sales",
        "bold": True, "fontcolor": "#666666", "fontsize": 14,
    },
    {"text": "© ", "fontsize": 14},
    {
        "text": "| sub-categories greater than <[Parameters].[Highlight Threshold]>% highlighted",
        "fontsize": 9,
    },
])
```

---

### Feature 4：折叠双轴 Bar（扩展现有 `configure_dual_axis`）

**对应脚本代码**：`build_bar_worksheet()`（第 1190–1457 行，~270 行 XML）

**当前问题**：`configure_dual_axis()` 已支持双轴，但缺少：
1. **折叠轴（fold axis）**：spacer 轴使用 `synchronized="true"` + `fold="true"`，并配合 `render-fold-reversed="true"` 实现 100% Bar 重叠效果。
2. **Measure Names 颜色编码**：Bar 工作表用 `[:Measure Names]` 驱动颜色。
3. **锚定 pane（anchor pane）**：第一个无 `x-axis-name` 的 pane 作为全局样式锚定，不能与常规 value pane 混淆。

#### 扩展现有接口（新增两个参数，向后完全兼容）

```python
def configure_dual_axis(
    self,
    ...  # 所有现有参数不变
    fold_axis: bool = False,               # 新增：第二轴使用折叠模式（render-fold-reversed）
    color_by_measure_names: bool = False,  # 新增：颜色编码用 [:Measure Names] 字段
) -> str:
```

`extra_axes` 参数的每个 axis dict 增加 `"fold": true` 支持：

```python
extra_axes=[
    {
        "field": "% Sales for Selected Region",
        "kind": "qk",
        "range_type": "fixed",
        "min": -0.07,
        "max": 1.02,
        "show": True,
    },
    {
        "field": "MIN(1) Bar",
        "kind": "qk",
        "fold": True,         # 新增：触发 fold=true + synchronized=true encoding
        "synchronized": True,
    },
]
```

**`builder_dual_axis.py` 内部修改**：

- 当 `fold_axis=True` 时，在 `<style-rule element="axis">` 的最后追加 `<format attr="render-fold-reversed" value="true"/>`。
- 当某 extra_axis 含 `"fold": True` 时，写 encoding 时加 `fold="true"` + `synchronized="true"` 属性，并省略 `range_type`/`min`/`max`。
- 当 `color_by_measure_names=True` 时，pane 中的 `<color>` encoding 写 `column="[ds_name].[:Measure Names]"` 而不是普通字段。

**重构后的脚本调用（~25 行替换 270 行）**：

```python
editor.configure_dual_axis(
    "Bar",
    mark_type_1="Bar",
    mark_type_2="Bar",
    columns=["LABEL:Bar * (% Sales for Selected Region + MIN(1) Bar)"],
    rows=["Sub-Category"],
    dual_axis_shelf="cols",
    color_by_measure_names=True,
    fold_axis=True,
    extra_axes=[
        {"field": "% Sales for Selected Region", "kind": "qk",
         "range_type": "fixed", "min": -0.07, "max": 1.02, "show": True},
        {"field": "MIN(1) Bar", "kind": "qk", "fold": True, "synchronized": True},
    ],
    label_1="% Sales for Selected Region",
    label_2="% Sales All Others",
    hide_axes=True, hide_zeroline=True,
    mark_sizing_off=True,
    size_value_1=BAR_MARK_SIZE,
    size_value_2=BAR_MARK_SIZE,
)
editor.configure_worksheet_style(
    "Bar",
    hide_gridlines=True, hide_zeroline=True, hide_table_dividers=True,
    cell_formats=[{"field": "Sub-Category", "height": 38}],
    header_formats=[{"height_header": 44}],
    label_formats=[
        {"field": ":Measure Names", "display": False},
        {"field": "Sub-Category", "display": False},
    ],
)
```

---

### Feature 5：多列表格工作表 `configure_multi_column_table`

**对应脚本代码**：`build_table_worksheet()`（第 706–1171 行，~470 行 XML）

这是**代码量最大**、**结构最复杂**的部分。该表格结构是 Tableau 中用 MIN(1)/MIN(0) spacer 技术实现的"伪表格"，核心结构为：

```
Cols shelf = (MIN1_subcat + MIN0_subcat) + (MIN1_A + MIN0_sales) + ...
Value pane = 有 x-axis-name、color + dual-text encoding、customized-label（bold run + normal run）
Spacer pane = 无 label，mark 透明（或特定颜色作分隔线）
```

#### 新增接口

```python
# src/cwtwb/charts/__init__.py  (ChartsMixin 新增方法)
# 实际逻辑在 src/cwtwb/charts/builder_table.py（新文件）

def configure_multi_column_table(
    self,
    worksheet_name: str,
    row_field: str,                    # 行字段，如 "Sub-Category"
    columns: list[TableColumn],        # 列定义列表（见下方数据类）
    color_field: Optional[str] = None, # 颜色字段，如 "Highlight"
    row_height: int = 38,
    header_height: int = 44,
    mark_size: str = "1.626187801361084",    # value pane 的 mark size
    spacer_size: str = "0.0099999997764825821",  # 透明 spacer 的 mark size
) -> str:
    """构建 MIN(1)/MIN(0) spacer 多列文本表格工作表。

    每个 TableColumn 代表一对 (value pane + header spacer pane)。
    这是 Tableau 实现跨多字段显示文本的标准 table-layout 技术。
    """
```

#### 配套数据类（新文件）

```python
# src/cwtwb/contracts/table_column.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class TableColumn:
    """多列表格中一列的配置。

    一列 = 一个 value pane（MIN(1) 轴）+ 一个 header spacer pane（MIN(0) 轴）。

    Attrs:
        header:        列标题文字（显示在 spacer pane 的轴标题上）。
        bold_field:    加粗文本的计算字段名（Highlight=True 时显示）。
        normal_field:  普通文本的计算字段名（Highlight=False 时显示）。
        axis_field:    value pane 的轴字段名（MIN(1) 类型计算字段，如 "MIN(1) A"）。
        spacer_field:  header spacer 的轴字段名（MIN(0) 类型计算字段，如 "MIN(0) Sales"）。
        instance_kind: column-instance 类型，"qk"(quantitative key) / "ok"(ordinal key) / "nk"(nominal key)。
        text_align:    文本对齐，"left" / "right" / "center"。
        vertical_align: 垂直居中，默认 False。
        spacer_color:  spacer 的颜色，None 表示透明（mark-transparency=0）。
        axis_index:    当同一轴字段被多列共用时的区分 index（如 "1"）。
                       对应 <pane x-index="1"> 属性。
        header_font:   标题字体名，如 "Tableau Book"（None 则不设置）。
    """
    header: str
    bold_field: str
    normal_field: str
    axis_field: str          # MIN(1) 计算字段名
    spacer_field: str        # MIN(0) 计算字段名
    instance_kind: str = "qk"
    text_align: str = "left"
    vertical_align: bool = False
    spacer_color: Optional[str] = None
    axis_index: Optional[str] = None
    header_font: Optional[str] = None
```

**重构后的脚本调用（~55 行替换 470 行）**：

```python
from cwtwb.contracts.table_column import TableColumn

editor.configure_multi_column_table(
    "Table",
    row_field="Sub-Category",
    color_field="Highlight",
    row_height=38,
    header_height=44,
    columns=[
        TableColumn(
            header="Sub-Category",
            bold_field="LABEL:Subcat BOLD",
            normal_field="LABEL:Subcat Normal",
            axis_field="MIN(1) Subcat",
            spacer_field="MIN(0) Subcat",
            instance_kind="nk",
            text_align="left",
        ),
        TableColumn(
            header="Sales",
            bold_field="LABEL:Sales BOLD",
            normal_field="LABEL:Sales Normal",
            axis_field="MIN(1) A",
            spacer_field="MIN(0) Sales",
            instance_kind="ok",
            text_align="right",
            vertical_align=True,
        ),
        TableColumn(
            header="Profit",
            bold_field="LABEL:Profit BOLD",
            normal_field="LABEL:Profit Normal",
            axis_field="MIN(1) A",    # 与 Sales 共用同一轴字段
            spacer_field="MIN(0) Profit",
            instance_kind="ok",
            text_align="right",
            vertical_align=True,
            axis_index="1",           # 区分同轴的第二个 pane
        ),
        TableColumn(
            header="Profit Ratio",
            bold_field="LABEL:Profit Ratio BOLD",
            normal_field="LABEL:Profit Ratio Normal",
            axis_field="MIN(1) B",
            spacer_field="MIN(0) Ratio",
            instance_kind="ok",
            text_align="right",
        ),
        TableColumn(
            header="Quantity",
            bold_field="LABEL:Qty BOLD",
            normal_field="LABEL:Qty Normal",
            axis_field="MIN(1) C",
            spacer_field="MIN(0) Qty",
            instance_kind="ok",
            text_align="right",
        ),
    ],
)
```

#### `builder_table.py` 内部实现职责

1. **字段收集与依赖声明**：通过 `field_registry` 解析所有 `axis_field`、`spacer_field`、`bold_field`、`normal_field`、`color_field` 为 `ColumnInstance`，构造 `<datasource-dependencies>` 中的 `<column>` + `<column-instance>` 节点，同时加入 row_field 和基础字段（Order Date、Region 等）。参考 `builder_base.py` 的 `_setup_datasource_dependencies`。

2. **`<style>` 区块**（按 element 分）：
   - `axis`：为每个 value pane 的轴写 space encoding（fixed range 0–1，无标题，高度 20）；为每个 spacer 轴写 fold encoding（fold=true, synchronized=true，标题=header 字符串，高度 20）；最后写 `tick-color=#00000000`。
   - `cell`：行高（`height` 对 row_field）。
   - `header`：列头高度（`height-header`）、total border 隐藏。
   - `label`：行字段标签隐藏（`display=false` 对 row_field）、行文本左对齐。
   - `pane`：total border 隐藏。
   - `gridline` / `zeroline` / `table-div`：全部关闭。
   - `axis-title`：spacer 字段的 `header_font` 设置。
   - `worksheet`：`display-field-labels=false` 对 cols。

3. **anchor pane**：无 `id` 无 `x-axis-name` 的 Bar pane，设置 `selection-relaxation-disallow`，style 中写 pane 的 minheight/maxheight/minwidth/maxwidth/aspect（固定尺寸锁定）和 datalabel 颜色。

4. **value pane 循环**（每个 `TableColumn`）：`id=N`、`x-axis-name=field(axis_field, "qk")`、可选 `x-index=axis_index`；encodings 含 `<color column=color_field>`、`<text column=bold_field>`、`<text column=normal_field>`；`<customized-label>` 含两个 run（bold + normal）；pane style 含 cell 对齐、datalabel 颜色/大小、mark 的 show/size/stroke 属性。

5. **spacer pane 循环**（每个 `TableColumn`）：`id=N`、`x-axis-name=field(spacer_field, "qk")`；无 encoding；pane style 的 mark 根据 `spacer_color` 分两种：有颜色则 mark-transparency=254，无颜色则 size=SPACER_SIZE + mark-transparency=0 + mark-color=#ffffff；pane 的 minheight=maxheight=-1。

6. **`<rows>` / `<cols>` 生成**：rows = row_field instance reference；cols = `_nested_sum(所有 axis + spacer fields 的 instance 引用)`（交替顺序：每列先 axis 后 spacer）。

---

## 三、仪表板布局扩展

### 3.1 现有能力覆盖情况

`add_dashboard(layout=dict)` + `layout.py` 的 zone 渲染已可表达大多数场景。

**WW33 仪表板层级**（用现有 layout dict 语法表达）：

```python
DASHBOARD_LAYOUT = {
    "type": "container",
    "direction": "vertical",
    "children": [
        # Title row（固定高度）
        {
            "type": "container",
            "direction": "horizontal",
            "fixed_size": 72,
            "children": [
                {"type": "worksheet", "name": "Title", "fixed_size": 555},  # 61667/111111*900≈500
                {
                    "type": "container",
                    "direction": "horizontal",
                    "children": [
                        {
                            "type": "filter",
                            "field": "Sub-Category",
                            "mode": "checkdropdown",  # Issue A
                            "show_apply": True,
                        },
                        {
                            "type": "paramctrl",
                            "param": "[Parameters].[Highlight Threshold]",
                            "mode": "type_in",        # Issue B
                            "custom_title": "Highlight Threshold",
                        },
                    ],
                },
            ],
        },
        # Content row
        {
            "type": "container",
            "direction": "horizontal",
            "children": [
                {"type": "worksheet", "name": "Table", "show_title": False},  # Issue D
                {"type": "worksheet", "name": "Bar",   "show_title": False},
            ],
        },
        # Footer text zones（3 个）— Issue C
        {
            "type": "text",
            "absolute": {"x": 889, "y": 91667, "w": 20333, "h": 7000},
            "runs": [
                {"text": "DESIGNED BY:", "bold": True, "fontcolor": "#333333", "fontsize": 8},
                {"text": "Corey Jones", "fontcolor": "#333333", "fontsize": 8},
            ],
        },
        ...
    ],
}
```

### 3.2 需要在 `layout.py` 中补充的 4 个细节

| Issue | 描述 | 修改位置 | 实现 |
|-------|------|---------|------|
| **A** | `filter` zone 的 `mode` 属性（`checkdropdown`/`dropdown`/`slider`） | `layout.py` → `_render_filter_zone()` | 若节点含 `"mode"` 键，写 `zone.set("mode", mode)` |
| **B** | `paramctrl` zone 的 `mode` 属性（`type_in`/`compact_slider`/`list`） | `layout.py` → `_render_paramctrl_zone()` | 同上，写 `mode` 属性 |
| **C** | `text` zone 支持绝对坐标（`absolute: {x, y, w, h}`） | `layout.py` → `generate_dashboard_zones()` | 当节点含 `"absolute"` 键时，跳过 layout 引擎的位置计算，直接用 absolute 值写 zone 属性 |
| **D** | worksheet zone 支持 `show_title: false` | `layout.py` → `_render_worksheet_zone()` | 若节点含 `"show_title": False`，写 `zone.set("show-title", "false")` |

---

## 四、重构后目标脚本骨架

重构后 `build_replication.py` 目标形态约 **300–380 行**，无任何 `lxml.etree` 操作：

```python
"""WW33 Table Formatting — cwtwb SDK 版"""
from __future__ import annotations
import json, datetime as _dt
from pathlib import Path
from cwtwb.twb_editor import TWBEditor
from cwtwb.contracts.table_column import TableColumn

# ── 路径 ──────────────────────────────────────────────────────────────
ITERATION_DIR  = Path(__file__).resolve().parent
INPUT_HYPER    = ITERATION_DIR / "inputs" / "Orders (Sample - Superstore).hyper"
TEMPLATE       = ...
OUTPUT_DIR     = ITERATION_DIR / "outputs"
DASHBOARD_NAME = f"2019_08_14_WW33_{_dt.datetime.now():%H%M%S}"

# ── 格式化字符串常量（保留）──────────────────────────────────────────
CURRENCY_FMT = 'c"$"#,##0;-"$"#,##0'
INT_FMT      = "n#,##0;-#,##0"
PCT_FMT      = "p0%"

# ── 内部字段名常量（保留，因业务逻辑需要）────────────────────────────
N_PARAM     = "[Parameter 1]"
N_PCT_SEL   = "[Calculation_PctSelectedRegion]"
# ... （其他内部名常量保留）

# ── CALCULATIONS 列表（保留，~100 行）────────────────────────────────
CALCULATIONS = [...]

# ── TABLE_COLUMNS 声明（替换原 TABLE_VALUE_PANES / TABLE_SPACER_PANES）
TABLE_COLUMNS = [
    TableColumn(header="Sub-Category", bold_field="LABEL:Subcat BOLD", ...),
    TableColumn(header="Sales",        bold_field="LABEL:Sales BOLD",  ...),
    TableColumn(header="Profit",       bold_field="LABEL:Profit BOLD", ..., axis_index="1"),
    TableColumn(header="Profit Ratio", bold_field="LABEL:Profit Ratio BOLD", ...),
    TableColumn(header="Quantity",     bold_field="LABEL:Qty BOLD",    ...),
]

# ── DASHBOARD_LAYOUT（替换原 build_dashboard 的 200 行 XML）──────────
DASHBOARD_LAYOUT = {
    "type": "container",
    "direction": "vertical",
    "sizing_mode": "fixed",
    "children": [
        {"type": "container", "direction": "horizontal", "fixed_size": 72,
         "children": [
             {"type": "worksheet", "name": "Title", "fixed_size": 555},
             {"type": "container", "direction": "horizontal", "children": [
                 {"type": "filter", "field": "Sub-Category",
                  "mode": "checkdropdown", "show_apply": True},
                 {"type": "paramctrl", "param": "[Parameters].[Highlight Threshold]",
                  "mode": "type_in", "custom_title": "Highlight Threshold"},
             ]},
         ]},
        {"type": "container", "direction": "horizontal",
         "children": [
             {"type": "worksheet", "name": "Table", "show_title": False},
             {"type": "worksheet", "name": "Bar",   "show_title": False},
         ]},
        {"type": "text", "absolute": {"x": 889, "y": 91667, "w": 20333, "h": 7000},
         "runs": [{"text": "DESIGNED BY:", "bold": True, "fontcolor": "#333333", "fontsize": 8},
                  {"text": "Corey Jones",  "fontcolor": "#333333", "fontsize": 8}]},
        # ... 其他 footer text zones
    ],
}

# ── build() ──────────────────────────────────────────────────────────
def build() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor = TWBEditor(TEMPLATE, clear_existing_content=True)
    editor.set_hyper_connection(str(INPUT_HYPER), table_name="Extract")

    # DS 名随机化（保留，约 20 行）
    ds_name = ...

    # 参数
    editor.add_parameter("Highlight Threshold", datatype="integer",
                         default_value="30", domain_type="any",
                         internal_name=N_PARAM)

    # 计算字段
    for caption, formula, datatype, role, ftype, fmt, internal in CALCULATIONS:
        editor.add_calculated_field(caption, formula, datatype=datatype,
                                    role=role, field_type=ftype,
                                    default_format=fmt, internal_name=internal)

    # 调色板（Feature 2）
    editor.set_datasource_color_palette(
        "Measure Names",
        color_map={f'"[{ds_name}].{inst(N_PCT_SEL,"qk")}"': "#5c6068",
                   f'"[{ds_name}].{inst(N_BAR_MIN1,"qk")}"': "#ffffff"},
        is_measure_names=True,
    )
    editor.set_datasource_color_palette(
        "Highlight",
        color_map={"true": "#d3d3d3", "false": "#ffffff"},
    )

    # 工作表
    for name in ("Title", "Table", "Bar"):
        editor.add_worksheet(name)
        editor.set_worksheet_hidden(name, hidden=True)

    # Title：动态标题（Feature 3）
    editor.set_worksheet_rich_title("Title", runs=[
        {"text": "<Order Date> <Region> Sales", "bold": True,
         "fontcolor": "#666666", "fontsize": 14},
        {"text": "© ", "fontsize": 14},
        {"text": "| sub-categories greater than <[Parameters].[Highlight Threshold]>% highlighted",
         "fontsize": 9},
    ])

    # Table：多列表格（Feature 5）
    editor.configure_multi_column_table(
        "Table", row_field="Sub-Category",
        color_field="Highlight", columns=TABLE_COLUMNS,
    )

    # Bar：折叠双轴（Feature 4）
    editor.configure_dual_axis(
        "Bar",
        mark_type_1="Bar", mark_type_2="Bar",
        columns=["LABEL:Bar * (% Sales for Selected Region + MIN(1) Bar)"],
        rows=["Sub-Category"],
        dual_axis_shelf="cols",
        color_by_measure_names=True,
        fold_axis=True,
        extra_axes=[...],
        label_1="% Sales for Selected Region",
        label_2="% Sales All Others",
        hide_zeroline=True, mark_sizing_off=True,
    )

    # 共享筛选器（Feature 1）
    editor.add_shared_filter("Region", values=["East"])
    editor.add_shared_filter("Sub-Category", all_members=True)
    editor.add_shared_filter("Order Date", year=2018)

    # 仪表板（现有 SDK + Issue A/B/C/D 补丁）
    editor.add_dashboard(DASHBOARD_NAME, width=900, height=600,
                         layout=DASHBOARD_LAYOUT,
                         worksheet_names=["Title", "Table", "Bar"])

    twb_path  = OUTPUT_DIR / "replicated-workbook.twb"
    twbx_path = OUTPUT_DIR / "replicated-workbook.twbx"
    editor.save(twb_path)
    editor.save(twbx_path)

    return {"twb": str(twb_path), "twbx": str(twbx_path),
            "worksheets": editor.list_worksheets(),
            "dashboards": editor.list_dashboards()}

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=False))
```

---

## 五、实现任务清单

按优先级和难度排序：

### P0 — 扩展 Bar 双轴（改动现有代码，难度低）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| B1 | `configure_dual_axis` 增加 `fold_axis` 参数 | `charts/__init__.py` + `builder_dual_axis.py` | axis encoding 增加 `fold="true"` + `synchronized="true"`；`_fmt(axis, "render-fold-reversed", "true")` |
| B2 | `configure_dual_axis` 增加 `color_by_measure_names` | `builder_dual_axis.py` | color encoding 字段写 `[ds_name].[:Measure Names]` |
| B3 | `extra_axes` 中支持 `"fold": True` | `builder_dual_axis.py` | encoding 时检查 `fold` 键，写对应属性，跳过 range/min/max |

### P1 — 共享筛选器（独立新功能，难度中）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| S1 | 实现 `add_shared_filter()` | `twb_editor.py` | 参考 `add_shared_views()` 逻辑；使用 `field_registry` 自动解析字段；`<shared-views>` 插入在 `<worksheets>` 前 |

### P2 — 数据源调色板（独立新功能，难度中）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| P1 | 实现 `set_datasource_color_palette()` | `twb_editor.py` | 参考 `add_datasource_palettes()` 逻辑；确保 `column-instance` 在 `<style>` 之前存在 |

### P3 — 富文本标题（扩展现有功能，难度低）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| T1 | 实现 `set_worksheet_rich_title(runs=[...])` | `twb_editor.py` | 扩展现有 `set_worksheet_title`；支持多 run + 字段引用解析为 CDATA；用正则识别 `<Field Name>` 模式 |

### P4 — 多列表格（全新功能，难度高）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| C1 | 新建 `TableColumn` 数据类 | `contracts/table_column.py`（新文件） | 纯 dataclass，无逻辑 |
| C2 | 新建 `TableChartBuilder` | `charts/builder_table.py`（新文件） | 参考 `builder_base.py` 基础设施；完整实现 §5 中的 6 个职责 |
| C3 | 注册 `configure_multi_column_table` | `charts/__init__.py` | 添加方法，路由到 `TableChartBuilder.build()` |
| C4 | 在 dispatcher 注册 | `charts/dispatcher.py` | 新增 `configure_multi_column_table` 分发函数 |

### P5 — 仪表板布局补丁（改动现有代码，难度低）

| # | 任务 | 文件 | 关键实现点 |
|---|------|------|-----------|
| D1 | filter zone 支持 `mode` 属性 | `layout.py` | `_render_filter_zone` 检查 `node.get("mode")`，写 `zone.set("mode", mode)` |
| D2 | paramctrl zone 支持 `mode` 属性 | `layout.py` | `_render_paramctrl_zone` 同上 |
| D3 | text zone 支持 `absolute` 坐标 | `layout.py` | `generate_dashboard_zones` 中检查 `"absolute"` 键，跳过 layout 计算直接写坐标 |
| D4 | worksheet zone 支持 `show_title: false` | `layout.py` | `_render_worksheet_zone` 检查 `show_title` 键，写 `zone.set("show-title", "false")` |

---

## 六、通用性说明

所有新增 API 均基于通用 Tableau 场景设计，不绑定 WW33 特定数据：

- **`add_shared_filter`** — 任何需要全局日期 / 地区 / 类别过滤的工作簿均可用
- **`set_datasource_color_palette`** — 任何需要自定义布尔字段或 Measure Names 颜色的工作簿均可用
- **`set_worksheet_rich_title`** — 动态标题在 Tableau 中普遍使用（数字 KPI、时间范围标题等）
- **`configure_multi_column_table`** — MIN(1)/MIN(0) spacer 表格是 WoW / Makeover Monday 中的高频技术，通用性强
- **`fold_axis` 扩展** — 100% Bar chart 是常见 viz 模式，`render-fold-reversed` 也用于其他折叠场景

---

*本文档由 Antigravity 生成，于 2026-08-04。*
