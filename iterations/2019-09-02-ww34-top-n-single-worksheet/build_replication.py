"""From-scratch build for WW34 "Top N Bar Chart on a Single Worksheet".

Protocol-compliant entry (docs/protocols/ai-case-iteration-protocol-draft.md):
  * 2.1 / 6.7 - build MUST start from the source template and clear all author
                 views; only the packaged original Hyper is reused.
  * cwtwb real API: TWBEditor(SOURCE_TWBX, clear_existing_content=True)
                 keeps the original Hyper datasource and DROPS every
                 worksheet/dashboard. We rebuild all views from the spec.

What the source does (reverse-engineered from the source .twbx, NOT copied
from its view XML):
  * 4 region top-N SETS over [Manufacturer], each ranking by SUM(region qty)
    with the [Top n Manufacturers] parameter driving the count:
        Top Central -> SUM(Central - Qty), Top East -> SUM(East - Qty),
        Top South -> SUM(South - Qty), Top West -> SUM(West - Qty).
  * [Manfacturer Category] classifies every Manufacturer into the region's
    top-N set or 'Other' (a single top-N-agnostic category).
  * [Index] = INDEX() with table-calc Field ordering (order by Region then
    Manfacturer Category, sort SUM(Quantity) DESC), so rows 1..N rank each
    region's manufacturers on ONE worksheet.
  * [FILTER Index] = Index <= Top n  (boolean, drives the row limit).
  * [FILTER - Other] = NOT(Include Other) AND Manfacturer Category = 'Other'
    (hides the Other row unless the parameter shows it).
  * [Index Rank] = '(#' + STR(Index) + ')' and
    [Manufacturer + Rank] = ATTR(Manfacturer Category) + ' ' + Index Rank.
  * [LABEL:Manufacturer] = IF ATTR(Highlighted Manufacturer) THEN
    Manufacturer + Rank ELSE ATTR(Manfacturer Category) END  -- a hover set
    action fills [Highlighted Manufacturer] and the GanttBar label switches
    to the "(#N)" ranked label.
  * [MIN(0)] = MIN(0) on the secondary GanttBar axis carrying that label.

The dual-axis view:  rows = [Index], cols = [Region] * (MIN(0) + SUM(Quantity)),
pane id=1 Bar on Quantity, pane id=2 GanttBar on MIN(0) with the LABEL text.
Two categorical filters: FILTER - Other = False, FILTER Index = True.
"""

from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree


ITERATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = ITERATION_DIR.parents[4]   # .../20260227-cwtwb  (cwtwb src + .env)
LAB_ROOT = ITERATION_DIR.parents[1]     # .../wow-tableau-problem-solving  (dashboards)
CWTwb_SRC = REPO_ROOT / "src"
sys.path.insert(0, str(CWTwb_SRC))

from cwtwb.twb_editor import TWBEditor  # noqa: E402


SOURCE_TWBX = (
    LAB_ROOT
    / "dashboards"
    / "2019_08_21_WW34_TopN_SingleWorksheet"
    / "2019_08_21_WW34_TopN_SingleWorksheet.twbx"
)
OUTPUT_DIR = ITERATION_DIR / "outputs"
EVIDENCE_DIR = ITERATION_DIR / "evidence"

DASHBOARD_NAME = "2019_08_21_WW34_TopN_Single_Sheet"


def _strip_author_intelligence(editor: "TWBEditor") -> None:
    """Remove the author's sets / calculated fields / parameters / styles.

    clear_existing_content=True only drops worksheet/dashboard views; the
    datasource still embeds the author's top-N SETS (<group filter-group>),
    calculated columns and a <style> block whose colour rules reference the
    deleted author calcs. Those encode the original solution logic, so for a
    clean from-scratch build we remove them and rebuild the field registry.
    The original Hyper connection + base-field metadata is preserved.
    """
    ds = editor._datasource

    removed_names: set[str] = set()

    # Remove author calculated columns (keep the synthetic [Number of Records]
    # constant Tableau auto-creates for every datasource).
    for col in list(ds.findall("column")):
        if col.find("calculation") is None:
            continue
        if col.get("name") == "[Number of Records]":
            continue
        removed_names.add(col.get("name"))
        ds.remove(col)

    # Remove the author's <group> SET definitions (filter-group sets).  These
    # are exactly what add_set() would otherwise collide with.
    for grp in list(ds.findall("group")):
        if grp.get("name-style") == "unqualified":
            removed_names.add(grp.get("name"))
            ds.remove(grp)

    # Remove author parameter columns.
    params_ds = editor.root.find("datasources/datasource[@name='Parameters']")
    if params_ds is not None:
        for col in list(params_ds.findall("column")):
            removed_names.add(col.get("name"))
            params_ds.remove(col)

    # Prune ONLY the metadata-records / column-instances that point at removed
    # author fields. Base-field metadata (Product Name, Quantity, Region, ...)
    # must be left intact or the field registry loses those fields.
    for mr in ds.findall(".//metadata-records/metadata-record"):
        ln = mr.find("local-name")
        if ln is not None and ln.text in removed_names and mr.getparent() is not None:
            mr.getparent().remove(mr)
    for dep in ds.findall("datasource-dependencies"):
        for ci in list(dep.findall("column-instance")):
            if ci.get("column") in removed_names:
                dep.remove(ci)
    # The datasource-level Parameters dependency block is stale after we
    # re-create the parameters; drop it (view-level deps are re-added).
    for dep in list(ds.findall("datasource-dependencies")):
        if dep.get("datasource") == "Parameters":
            ds.remove(dep)

    # Remove the orphaned datasource <style> (author colour rules referencing
    # deleted calcs). We re-add a Region palette ourselves.
    old_style = ds.find("style")
    if old_style is not None:
        ds.remove(old_style)

    if params_ds is not None:
        pstyle = params_ds.find("style")
        if pstyle is not None:
            params_ds.remove(pstyle)

    # Order matters: _init_parameters() rebuilds the parameter registry
    # (clearing the author's entries) and _reinit_fields() restores the base
    # fields from the (untouched) connection metadata. _init_parameters() must
    # run first; then _reinit_fields().
    editor._init_parameters()
    editor._reinit_fields()


def _local(editor: "TWBEditor", display_name: str) -> str:
    """Return the bracketed internal TWB name for a registered field."""
    return editor.field_registry._find_field(display_name).local_name


def _apply_cols_join(editor: "TWBEditor", ws_name: str) -> None:
    """Rewrite the cols shelf so the leading dimension CROSSES the dual-axis
    fold with ``*`` instead of the builder's ``+`` (side-by-side).

    Tableau serializes dimension x (dual-axis measures) on the columns shelf
    as ``([dim] * ([m1] + [m2]))``.  A ``+`` between the dimension and the
    fold is parsed as two juxtaposed shelves, which renders the region headers
    beside the measures instead of overlaid per region.
    """
    ws = editor._find_worksheet(ws_name)
    table = ws.find("table")
    cols_el = table.find("cols")
    if cols_el is None or not (cols_el.text or "").strip():
        return
    text = cols_el.text.strip()
    marker = "] + (["
    if marker in text and "] * ([" not in text:
        cols_el.text = text.replace(marker, "] * ([", 1)


def _apply_index_table_calc_ordering(editor: "TWBEditor", ws_name: str) -> None:
    """Inject the source's table-calc Field ordering for the per-region rank.

    The source drives INDEX() ranking on ONE worksheet with an instance-level
    table-calc:
        <table-calc level-break='[ds].[Manfacturer Category]'
                    ordering-type='Field'>
          <order field='[ds].[Region]' />
          <order field='[ds].[Manfacturer Category]' />
          <sort direction='DESC' using='[ds].[sum:Quantity:qk]' />
        </table-calc>
    cwtwb's builder only copies the calc-level ``ordering-type`` (Rows); the
    Field addressing is instance-level authoring cwtwb cannot express through
    its table_calc param, so we reproduce it here.  The dependent instances
    (FILTER Index, Index Rank, Manufacturer + Rank, LABEL:Manufacturer) carry
    their own ``ordering-type='Columns'`` plus a nested Index dependency with
    the same Field ordering, exactly as the source publishes.
    """
    ws = editor._find_worksheet(ws_name)
    table = ws.find("table")
    view = table.find("view")
    ds_name = editor._datasource.get("name", "")

    idx_local = _local(editor, "Index")
    idx_rank_local = _local(editor, "Index Rank")
    manf_rank_local = _local(editor, "Manufacturer + Rank")
    label_local = _local(editor, "LABEL:Manufacturer")
    filt_idx_local = _local(editor, "FILTER Index")
    cat_local = _local(editor, "Manfacturer Category")
    region_inst = "[none:Region:nk]"
    qty_inst = "[sum:Quantity:qk]"

    dd = view.find(f"datasource-dependencies[@datasource='{ds_name}']")
    if dd is None:
        return

    instances = {ci.get("column"): ci for ci in dd.findall("column-instance")}

    def field_ordering(extra_field: str = "") -> etree._Element:
        tc = etree.Element("table-calc")
        if extra_field:
            tc.set("field", extra_field)
        tc.set("level-break", f"[{ds_name}].{cat_local}")
        tc.set("ordering-type", "Field")
        order_region = etree.SubElement(tc, "order")
        order_region.set("field", f"[{ds_name}].{region_inst}")
        order_cat = etree.SubElement(tc, "order")
        order_cat.set("field", f"[{ds_name}].{cat_local}")
        sort = etree.SubElement(tc, "sort")
        sort.set("direction", "DESC")
        sort.set("using", f"[{ds_name}].{qty_inst}")
        return tc

    def clear_table_calcs(ci: etree._Element) -> None:
        for tc in list(ci.findall("table-calc")):
            ci.remove(tc)

    # --- Index instance: the field ordering itself ------------------------
    index_ci = instances.get(idx_local)
    if index_ci is not None:
        clear_table_calcs(index_ci)
        index_ci.append(field_ordering())

    # --- Dependent instances: self Columns ordering + nested Index dep -----
    idx_dep_ref = f"[{ds_name}].{idx_local}"
    for local, nested_refs in (
        (filt_idx_local, ()),
        (idx_rank_local, ()),
        (manf_rank_local, (idx_rank_local,)),
        (label_local, (manf_rank_local, idx_rank_local)),
    ):
        ci = instances.get(local)
        if ci is None:
            continue
        clear_table_calcs(ci)
        self_tc = etree.SubElement(ci, "table-calc")
        self_tc.set("ordering-type", "Columns")
        for ref in nested_refs:
            dep_tc = etree.SubElement(ci, "table-calc")
            dep_tc.set("field", f"[{ds_name}].{ref}")
            dep_tc.set("ordering-type", "Columns")
        ci.append(field_ordering(extra_field=idx_dep_ref))


def _ensure_slices(editor: "TWBEditor", ws_name: str) -> None:
    """Add the two boolean filter columns to <slices> (as the source does)."""
    ws = editor._find_worksheet(ws_name)
    table = ws.find("table")
    view = table.find("view")
    ds_name = editor._datasource.get("name", "")
    dd = view.find(f"datasource-dependencies[@datasource='{ds_name}']")
    if dd is None:
        return
    filter_inst_names = []
    for ci in dd.findall("column-instance"):
        col = ci.get("column", "")
        if col == _local(editor, "FILTER - Other") or col == _local(editor, "FILTER Index"):
            filter_inst_names.append(ci.get("name"))
    slices_el = view.find("slices")
    if slices_el is None:
        slices_el = etree.Element("slices")
        agg_el = view.find("aggregation")
        if agg_el is not None:
            agg_el.addprevious(slices_el)
        else:
            view.append(slices_el)
    existing = {c.text for c in slices_el.findall("column")}
    for inst in filter_inst_names:
        ref = f"[{ds_name}].{inst}"
        if ref not in existing:
            col = etree.SubElement(slices_el, "column")
            col.text = ref


def _package_twbx(twb_path: Path, output_twbx: Path) -> None:
    """Repackage the built .twb with the original Hyper into a .twbx."""
    output_twbx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SOURCE_TWBX, "r") as src:
        hyper_names = [n for n in src.namelist()
                       if n.lower().endswith(".hyper") or n.lower().endswith(".tde")]
        with zipfile.ZipFile(output_twbx, "w", zipfile.ZIP_DEFLATED) as out:
            out.write(twb_path, "Book1.twb")
            for h in hyper_names:
                out.writestr(h, src.read(h))


def build(output_twb: Path, output_twbx: Path) -> Path:
    # From-scratch entry: keep original Hyper, drop all author views.
    editor = TWBEditor(SOURCE_TWBX, clear_existing_content=True)
    _strip_author_intelligence(editor)

    # --- Parameters -------------------------------------------------------
    editor.add_parameter(
        "Top n Manufacturers",
        datatype="integer",
        default_value="15",
        domain_type="range",
        min_value="1",
        max_value="100",
        granularity="1",
    )
    editor.add_parameter(
        "Include Other",
        datatype="boolean",
        default_value="false",
        domain_type="list",
        allowed_values=["true", "false"],
        allowed_aliases={"true": "YES", "false": "NO"},
    )

    # --- Calculated fields (dependencies first) ---------------------------
    editor.add_calculated_field(
        "Manufacturer",
        "MID([Product Name],1, FINDNTH([Product Name],' ',1)-1)",
        datatype="string",
    )
    for region in ("Central", "East", "South", "West"):
        editor.add_calculated_field(
            f"{region} - Qty",
            f"IF [Region] = '{region}' THEN [Quantity] END",
            datatype="integer",
        )

    # Manfacturer Category: references the four top-N sets by name.  The sets
    # are created below; unresolved references stay as their clean bracket
    # names, which is exactly the sets' internal name, so they resolve.
    editor.add_calculated_field(
        "Manfacturer Category",
        "IF [Region]='Central' AND [Top Central] THEN [Manufacturer] "
        "ELSEIF [Region]='East' AND [Top East] THEN [Manufacturer] "
        "ELSEIF [Region]='South' AND [Top South] THEN [Manufacturer] "
        "ELSEIF [Region]='West' AND [Top West] THEN [Manufacturer] "
        "ELSE 'Other' END",
        datatype="string",
    )

    # Index is ordinal so the rows shelf renders discrete 1..N row headers.
    editor.add_calculated_field(
        "Index",
        "INDEX()",
        datatype="integer",
        field_type="ordinal",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Index Rank",
        "'(#' + STR([Index]) + ')'",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "Manufacturer + Rank",
        "ATTR([Manfacturer Category]) + ' ' + [Index Rank]",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "FILTER Index",
        "[Index] <= [Top n Manufacturers]",
        datatype="boolean",
        table_calc="Rows",
    )
    editor.add_calculated_field(
        "FILTER - Other",
        "NOT([Include Other]) AND [Manfacturer Category] = 'Other'",
        datatype="boolean",
        role="dimension",
    )
    editor.add_calculated_field(
        "LABEL:Manufacturer",
        "IF ATTR([Highlighted Manufacturer]) THEN [Manufacturer + Rank] "
        "ELSE ATTR([Manfacturer Category]) END",
        datatype="string",
        table_calc="Rows",
    )
    editor.add_calculated_field("MIN(0)", "MIN(0)", datatype="integer")

    # --- Sets -------------------------------------------------------------
    editor.add_set(
        "Top Central",
        "Manufacturer",
        basis_field="Central - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top East",
        "Manufacturer",
        basis_field="East - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top South",
        "Manufacturer",
        basis_field="South - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Top West",
        "Manufacturer",
        basis_field="West - Qty",
        aggregation="Sum",
        top_n="Top n Manufacturers",
        direction="DESC",
    )
    editor.add_set(
        "Highlighted Manufacturer",
        "Manfacturer Category",
    )

    # --- Worksheet: dual axis on columns ----------------------------------
    editor.add_worksheet("Viz")
    editor.configure_dual_axis(
        "Viz",
        mark_type_1="Bar",
        mark_type_2="GanttBar",
        # cols[-2] (SUM(Quantity)) -> pane id=1 (Bar), cols[-1] (MIN(0)) ->
        # pane id=2 (GanttBar).  Region is the leading dimension.
        columns=["Region", "SUM(Quantity)", "[MIN(0)]"],
        rows=["Index"],
        dual_axis_shelf="columns",
        synchronized=True,
        color_1="Region",
        detail_1="Manfacturer Category",
        color_2="Region",
        detail_2="Manfacturer Category",
        label_2="LABEL:Manufacturer",
        filters=[
            {"column": "FILTER - Other", "values": [False]},
            {"column": "FILTER Index", "values": [True]},
        ],
        color_map_1={
            "South": "#027b8e",
            "East": "#6fb899",
            "Central": "#8175aa",
            "West": "#9f8f12",
        },
    )

    # Reproduce the source's instance-level table-calc Field ordering so
    # INDEX() ranks within each region (10 rows per region at Top n=10).
    _apply_index_table_calc_ordering(editor, "Viz")
    # Region must CROSS the dual-axis fold on the cols shelf (source uses `*`).
    _apply_cols_join(editor, "Viz")
    # The two boolean filters also live in <slices> in the source.
    _ensure_slices(editor, "Viz")

    # --- Dashboard --------------------------------------------------------
    footer_runs = [
        {"text": "DESIGNED BY : ", "bold": True, "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "Jeffrey A. Schaffer", "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "  |  ", "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "#WORKOUTWEDNESDAY", "bold": True, "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "  |  2019  |  WEEK 34", "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "  |  RECREATED BY : ", "bold": True, "font_size": "8", "font_color": "#1b1b1b"},
        {"text": "Donna Coles", "font_size": "8", "font_color": "#1b1b1b"},
    ]

    layout = {
        "type": "container",
        "direction": "vertical",
        "children": [
            {
                "type": "container",
                "direction": "horizontal",
                "children": [
                    {"type": "worksheet", "name": "Viz", "weight": 8},
                    {
                        "type": "container",
                        "direction": "vertical",
                        "fixed_size": 184,
                        "children": [
                            {"type": "paramctrl", "parameter": "Include Other",
                             "mode": "compact"},
                            {"type": "paramctrl", "parameter": "Top n Manufacturers",
                             "mode": "type_in"},
                        ],
                    },
                ],
            },
            {"type": "text", "runs": footer_runs, "fixed_size": 60},
        ],
    }
    editor.add_dashboard(
        DASHBOARD_NAME,
        width=1000,
        height=800,
        layout=layout,
        worksheet_names=["Viz"],
    )

    # --- Set Action (on-hover fills Highlighted Manufacturer) --------------
    editor.add_dashboard_set_action(
        DASHBOARD_NAME,
        source_sheet="Viz",
        target_set="Highlighted Manufacturer",
        event_type="on-hover",
        caption="Highlight Rank",
        clear_option="exclude-all",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    editor.save(output_twb, validate=False)
    _package_twbx(output_twb, output_twbx)

    _write_provenance(output_twb)
    return output_twb


def _write_provenance(output_twb: Path) -> None:
    """Record machine-readable build provenance (protocol 10.2)."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    provenance = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "build_inputs": [
            "specs/replication-spec.yaml",
            "specs/solution-graph.yaml",
            "dashboards/2019_08_21_WW34_TopN_SingleWorksheet/2019_08_21_WW34_TopN_SingleWorksheet.twbx (data: original Hyper only)",
        ],
        "source_twbx_read_during_build": True,
        "source_used_as": "datasource_carrier_for_original_hyper",
        "author_view_xml_copied": False,
        "clear_existing_content": True,
        "forbidden_inputs_observed": [],
        "from_scratch": True,
        "functional_elements": [
            "Top n Manufacturers integer parameter (default 15, range 1-100)",
            "Include Other boolean parameter (default false, aliases YES/NO)",
            "Four region top-N sets over Manufacturer (Central/East/South/West - Qty)",
            "Highlighted Manufacturer empty set (Set Action target)",
            "Manfacturer Category: region top-N membership or 'Other'",
            "Index = INDEX() with Field ordering (per-region rank on one sheet)",
            "FILTER Index = Index <= Top n; FILTER - Other hides Other row",
            "LABEL:Manufacturer = ranked '(#N)' label when hovered set fills",
            "Dual-axis worksheet Viz: rows=Index, cols=Region * (MIN(0) + SUM(Quantity)), Bar + GanttBar",
            "Dashboard with compact Include Other + type_in Top n paramctrl",
            "on-hover Set Action 'Highlight Rank' -> Highlighted Manufacturer (exclude-all)",
        ],
        "deviations_from_source": [
            "Set internal names are unified (Top Central/East/South/West) "
            "instead of the source's 'Top Central (copy)'/'Top East (copy)' "
            "internal names; display captions match the source exactly.",
            "Top n Manufacturers parameter is emitted with domain_type=range "
            "1-100 per the replication spec; the source serializes the domain "
            "as 'any'.",
            "The INDEX() instance-level Field table-calc (level-break/order/"
            "sort) is reproduced in _apply_index_table_calc_ordering; cwtwb's "
            "table_calc API cannot author instance-level addressing natively.",
            "The cols shelf join between Region and the dual-axis fold is "
            "'*' (as the source) via _apply_cols_join; cwtwb's dual-axis "
            "builder emits '+' by default.",
        ],
        "known_visual_gaps": [
            "Axis/style formatting (axis strokes, gridlines, header widths) "
            "uses cwtwb defaults rather than the source's exact pixel styles.",
            "The 'Data' hidden helper worksheet from the source is omitted "
            "(maximum_visible_worksheets allows 1 visible sheet).",
        ],
    }
    (EVIDENCE_DIR / "build-provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    print(build(OUTPUT_DIR / "replicated-workbook.twb",
                OUTPUT_DIR / "replicated-workbook.twbx"))
