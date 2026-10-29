# Customer purchasing habits: analysis checkpoint

Identity confirmed using scripts/case_intake.py: article 2021-11-11, official challenge 2021-11-10, week 45 of 2021.

Business question: compare customer purchasing recency, frequency, spend, average order value and quantity; identify active customers and inspect their leading products.

Article and author calculations agree on fixed reference date 2022-01-01, never system today. Recency is days from customer-level maximum order date. Active means recency <= threshold, initially 90. Exactly 90 is active; 91 is inactive. Labels use days below 365 and years (days/365, one decimal) at or above 365. Frequency is COUNTD(Order ID), monetary value SUM(Sales), AOV SUM(Sales)/COUNTD(Order ID); quantity is SUM(Quantity), distinct products COUNTD(Product ID). Group by Customer ID, not name alone.

Five sort choices: recency ascending; order count, sales, AOV, quantity descending. Author uses SUM(recency) in sort, which can weight recency by line count; independently establish intended customer-level sort rather than blindly copying it.

Quantity circle tooltip must show top ten products by customer sales, filtered by Customer ID, with sales, quantity and rank. Article describes unique ranking but author Sales Rank formula is RANK(SUM(Sales)); ties need explicit verification. Dashboard has six aligned headings, parameter controls, and show/hide help button (?/X).

Only packaged Hyper data extracted by prepare_case.py. No author XML is permitted in builder. Baseline SDK must be explicitly selected at scratch/sdk-release-0.29.0a2 in original checkout.

Pending: read official challenge body, inspect raw Hyper schema, build from blank, independent numerical oracle, contract and negative tests, SDK baseline execution, local validation and repository tests. Desktop, Cloud, live interactions and independent review belong to parent. No SDK gap has yet been demonstrated.

## Completed implementation discovery
Official challenge body retrieved 2026-10-29 confirms 1600x900, five metrics, configurable active flag, metric sorting, and product tooltip. Fixed date explicitly 2022-01-01. No quintile segmentation is requested: active/inactive is the required segment. Raw extract has 9994 lines and 793 customers. Public baseline APIs support layered panes, computed customer sort, parameter controls and context-filtered tooltip. Builder uses raw Hyper directly; verifier independently aggregates Hyper SQL and evaluates emitted expressions, without importing builder. Article help toggle and explicit product rank remain unimplemented, not attributed to an SDK gap. Product-name grouping follows the article; unique-product count uses Product ID. Ties have no specified secondary ordering.

## Completion of article interactions (supersedes earlier omissions)
Help now uses a text worksheet inside a floating container and the public native show/hide API, initially hidden with ?/X states. Product Rank is RANK_UNIQUE(SUM(Sales), desc), displayed as the first measure with a # prefix; a table calculation filter keeps ranks 1 through 10 after customer context filtering. Product Name is the sole row dimension, so Rows addressing computes within the filtered customer. This follows the article instruction to select unique ranking; the author archive RANK formula conflicts with that instruction. Tied values get distinct consecutive ranks, without promising which tied product is chosen at tenth position. A tied fixture covers both first and tenth positions; independent raw SQL ROW_NUMBER verifies 9941 customer/product groups using name as an oracle-only tie breaker.
Six explicit heading zones each have width 260 pixels across the 1560-pixel sheet region. Customer header and metric cell widths also explicitly request 260. Runtime font, scrollbar and Tableau sizing still need visual checking. All three omitted features now build with public a2 APIs; no capability gap is claimed.

## Runtime P1 diagnosis and correction
Parent screenshot inspected directly: customer names and Abc only, no five metrics. Runtime CSV confirms only Customer ID, Customer Name and Sort Key. The failed a89757a4 artifact has an empty table/cols although pane x-axis references and their dependencies exist. Public layered API builds the shelf from columns, not panes; omission in case builder is root cause, not an SDK capability gap. Added the explicit five expressions to columns. Strengthened verifier checks exact ordered shelf/axis correspondence, additive independent axes and quantitative instance/column resolution. It rejects the preserved real failing workbook. Replacement has not been rendered; parent runtime recapture is mandatory.

## Rank runtime P1 correction
Parent reports 1849 products all rank 1. Rows addressing is not evidence of Product Name addressing in this table. Replaced ordinary measure-values chart with public configure_layered_chart, explicit Field/Product Name override, and table_calc_context=True. Filter references the addressed rank instance. No reusable SDK blocker established: released a2 emits the explicit configuration. Previous sequential rank evaluator removed; raw SQL ROW_NUMBER is an expectation oracle, not evidence that Tableau executed ranking. Parent must test global plus two customer contexts. Recency uses a string calculation with explicit days/years suffix instead of default formats; sort parameter holds human-readable strings, preserving same five sort keys and default. Help uses ASCII sentence text without literal newline escape; hide_axes is also set through worksheet style API.
