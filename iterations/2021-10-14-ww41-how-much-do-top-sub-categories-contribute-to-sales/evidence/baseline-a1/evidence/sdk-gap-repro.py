"""Author-free a1 reproductions; no generated XML mutations or external data."""
import json
import cwtwb
from cwtwb import TWBEditor

results = {"version": cwtwb.__version__, "gaps": []}

def editor():
    e = TWBEditor("")
    e.add_calculated_field("Category", "'A'", datatype="string", role="dimension")
    e.add_calculated_field("Value", "1")
    e.add_calculated_field("Axis", "MIN(0)")
    e.add_parameter("Top N", datatype="integer", default_value="1")
    e.add_set("Top Set", dimension_field="Category", basis_field="Value", top_n="Top N")
    e.add_calculated_field("Label", "IF [Top Set] THEN 'Top' ELSE 'Other' END", datatype="string", role="dimension")
    e.add_worksheet("Pie")
    return e

e = editor()
e.configure_dual_axis("Pie", rows=["Axis", "Axis"], mark_type_1="Pie", mark_type_2="Pie", color_1="Category", color_2="Label", wedge_size_1="SUM(Value)", wedge_size_2="SUM(Value)")
try:
    e.configure_custom_label("Pie", [{"field": "Label"}], pane_index=2)
except ValueError as exc:
    assert "No datasource column for [Top Set]" in str(exc)
    results["gaps"].append({"id": "rich-label-set-dependency", "reproduced": True, "error": str(exc)})
else:
    raise AssertionError("Expected a1 set dependency error was not reproduced")

e = editor()
try:
    e.configure_dual_axis("Pie", rows=["Axis", "Axis"], mark_type_1="Pie", mark_type_2="Pie", color_1="Category", color_2="Label", wedge_size_1="SUM(Value)", wedge_size_2="SUM(Value)", sort_field="Category", sort_descending="SUM(Value)")
except ValueError as exc:
    assert "sort_field must identify a dimension on the row shelf" in str(exc)
    results["gaps"].append({"id": "dual-axis-color-sort", "reproduced": True, "error": str(exc)})
else:
    raise AssertionError("Expected a1 color-sort error was not reproduced")
print(json.dumps(results, indent=2))
