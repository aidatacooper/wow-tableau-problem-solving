# Problem Model — 2019 WW34 Top N Bar Chart on a Single Worksheet

> 仅依据文章 `posts/2019-09-02-Can_you_build_a_Top_N_Bar_Chart_on_a_Single_Worksheet.html`
> 与案例元数据回答。本阶段不讨论 cwtwb API。

## 1. 用户最终要做什么判断？

在**单张 worksheet** 上同时比较四个 Region 各自 **Quantity 排名前 N 的
Manufacturer** 的销量表现，其中：

- 每个 Region 独立计算自己的 Top N 制造商集合；
- 各 Region 未进前 N 的制造商全部折叠进该 Region 的 **"Other"** 桶；
- 同一制造商在不同 Region 的排名与归属可以不同；
- 用户能通过参数切换 N（Top n Manufacturers）和是否显示 Other（Include Other）；
- 把鼠标悬停在某根 bar 上时，能**同时看到 Manufacturer 名和它在当前 Region 的
  排名**（hover 高亮排名）。

## 2. 普通方法为什么不够 / 会算错？

- 直接对全部数据做「Top N」只能得到**全局** Top N，做不到「每 Region 各自的
  Top N + 各 Region 的 Other」。
- 简单的 top-filter 会把一个 Region 的 Top 制造商当成其他 Region 的 Top，无法
  表达「Wilson 在 East/West 是 Top10、在 Central/South 却是 Other」。
- 若为每个 Region 各建一个 worksheet，又违背「Single Worksheet」的核心约束。
- 若用 `RANK()` 表计算做过滤，在视图内按 Region 分区后还需要对「Other」单独
  聚合，且无法为 hover 提供「当前行是哪个制造商 + 排第几」的动态标签。

## 3. 正确结果必须表现出的行为

1. 四个 Region 并排，每 Region 内按 Quantity 降序显示其 Top N 制造商；
2. 每个 Region 的 Other 桶 = 该 Region 前 N 名之外的所有制造商 Quantity 之和；
3. `Top n Manufacturers` 参数（默认 15）改变时，行数、集合成员和 Other 值随之
   重新计算；
4. `Include Other` 参数（默认 NO）为 YES 时显示 Other 行，为 NO 时隐藏；
5. INDEX() 表计算按「Region 内 SUM(Quantity) 降序」给每行编号，行数上限由参数
   控制；
6. hover 任意 bar：该行标签从「Manufacturer 名」切换为「Manufacturer 名 (#排名)」，
   移出后恢复——由 Set Action 填充 `Highlighted Manufacturer` 集合实现。

## 4. 必要 BI 语义（required）

- 作者原始 Hyper（Superstore，含 Product Name / Region / Quantity）；
- `Manufacturer` = `MID([Product Name],1, FINDNTH([Product Name],' ',1)-1)`
  （产品名第一个词；Superstore 无原生 Manufacturer 字段）；
- 每 Region 一个 Top N **集合**（Top Central / East / South / West），各基于
  Region 内 Quantity 汇总；
- `Manfacturer Category`：命中所属 Region 的 Top N 集合则返回 Manufacturer，
  否则 `'Other'`；
- `Top n Manufacturers` 参数（int，默认 15）、`Include Other` 参数（bool，默认 NO）；
- `Index` = `INDEX()`（Region 内按 SUM(Quantity) 降序编号）；
- `FILTER Index` = `[Index] <= [Top n Manufacturers]`；
- `FILTER - Other` = `NOT([Include Other]) AND [Manfacturer Category]='Other'`；
- `Index Rank` = `'(#' + STR([Index]) + ')'`；
- `Manufacturer + Rank` = `ATTR(Category) + ' ' + Index Rank`；
- `Highlighted Manufacturer` 集合 + **Set Action**（on-hover，clear=exclude-all）；
- `LABEL:Manufacturer` = `IF ATTR([Highlighted Manufacturer]) THEN (Manu+Rank)
  ELSE ATTR(Category) END`；
- 同步双轴：`Index` 在 rows，`Region × (MIN(0) GanttBar 标签轴 + SUM(Quantity)
  Bar 轴)` 在 cols；
- Dashboard：1 个可见 Viz sheet + 2 个参数控件（Top n / Include Other）。

## 5. 可替代实现（replaceable）

- Region Top N 集合可用「Top N by 字段」集合，也可用 FIXED LOD + RANK 表计算
  构造数值等价方案（不显示 hover 排名时）；
- "Other" 聚合可用参数化的 `IF [Index] <= N THEN [Category] ELSE 'Other' END` 表达；
- 隐藏的 `Data` 核对 sheet 仅用于调试，可省略。

## 6. 仅视觉装饰（presentation_only）

- Nuriel Stone 调色板、字体字号、署名/页脚文字、header 宽度、行高、网格线、
  隐藏 axis 等逐像素格式。
