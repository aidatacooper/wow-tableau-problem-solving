"""Independently build the survey dashboard from the locked Hyper extract."""
from pathlib import Path
from cwtwb import TWBEditor
from tableauhyperapi import HyperProcess, Connection, Telemetry, CreateMode, TableDefinition, TableName, SqlType, Inserter

HERE = Path(__file__).resolve().parent
DASHBOARD = "2021_08_11_WOW32_Survey_Data"
TRACK = "Which track do you participate in?"
FREQUENCY = "How Often Do You Participate"
SENTIMENT = [
    "I enjoy learning about new features",
    "I want more cross-over with other software and/or platforms",
    "The challenges are too difficult", "The challenges are too easy",
    "The challenges help me at work/school",
]
CHOICES = [f"What do you want more of?  (Rank Your Choices) ({n})"
           for n in ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th")]
COLORS = {"Strongly Disagree": "#c24e00", "Disagree": "#f4a259",
          "Neither Agree nor Disagree": "#dddddd", "Agree": "#9d94c5",
          "Strongly Agree": "#675493"}


def build():
    e = TWBEditor("")
    # Duplicate each response for the two donut slices; COUNTD preserves all
    # other sheets' respondent counts. This avoids unsupported layered pie
    # Measure Values angle binding without editing generated XML.
    source = HERE / "inputs/TEMP_12e3vxa1smragy1a5pxzg0cjmlrx.hyper"
    scaffold = HERE / "outputs/survey-slices.hyper"
    scaffold.parent.mkdir(exist_ok=True)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as h:
        with Connection(h.endpoint, str(source)) as c:
            table = c.catalog.get_table_names("Extract")[0]
            columns = list(c.catalog.get_table_definition(table).columns)
            records = c.execute_list_query(f"SELECT * FROM {table}")
        with Connection(h.endpoint, str(scaffold), CreateMode.CREATE_AND_REPLACE) as c:
            c.catalog.create_schema("Extract")
            target = TableDefinition(TableName("Extract", "Extract"), columns + [TableDefinition.Column("Slice", SqlType.text())])
            c.catalog.create_table(target)
            with Inserter(c, target) as ins:
                ins.add_rows([list(row) + [slice_name] for row in records for slice_name in ("Track", "Other")])
                ins.execute()
    e.set_hyper_connection(str(scaffold))
    def calc(name, formula, addressing=None, datatype="real", role="measure", field_type="quantitative"):
        kwargs = dict(datatype=datatype, role=role, field_type=field_type)
        if addressing:
            kwargs["table_calc"] = {"ordering_type": "Field", "ordering_field": f"[{addressing}]"}
        if datatype == "real":
            kwargs["default_format"] = "p0%"
        e.add_calculated_field(name, formula, **kwargs)
    calc("Respondents", "COUNTD([Respondent])", datatype="integer")
    calc("Track Share", "COUNTD([Respondent])/TOTAL(COUNTD([Respondent]))", TRACK)
    calc("Other Track Share", "1-[Track Share]", TRACK)
    calc("Slice Share", "IF ATTR([Slice])='Track' THEN [Track Share] ELSE 1-[Track Share] END", TRACK)
    calc("Participation Share", "COUNTD([Respondent])/TOTAL(COUNTD([Respondent]))", FREQUENCY)
    calc("Answer Share", "COUNTD([Respondent])/TOTAL(COUNTD([Respondent]))", "Answer")
    calc("Positive Share", "CASE ATTR([Answer]) WHEN 'Agree' THEN [Answer Share] WHEN 'Strongly Agree' THEN [Answer Share] WHEN 'Neither Agree nor Disagree' THEN [Answer Share]/2 END", "Answer")
    calc("Negative Share", "CASE ATTR([Answer]) WHEN 'Disagree' THEN -[Answer Share] WHEN 'Strongly Disagree' THEN -[Answer Share] WHEN 'Neither Agree nor Disagree' THEN -[Answer Share]/2 END", "Answer")
    calc("Answer Rank", "RANK_UNIQUE(COUNTD([Respondent]),'desc')", "Answer", datatype="integer", field_type="ordinal")
    calc("Answer Order", "CASE [Answer] WHEN 'Strongly Disagree' THEN 5 WHEN 'Disagree' THEN 4 WHEN 'Neither Agree nor Disagree' THEN 3 WHEN 'Agree' THEN 2 WHEN 'Strongly Agree' THEN 1 END", datatype="integer")
    calc("Ring", "MIN(1)", datatype="integer")
    calc("Hole", "MIN(1)", datatype="integer")
    e.set_datasource_color_palette("Answer", COLORS)
    sheets = ["Donuts", "Bar-Participate", "Bar-Diverging", "Bar-Vertical", "Heatmap"]
    for sheet in sheets:
        e.add_worksheet(sheet)
    e.configure_dual_axis("Donuts", columns=[TRACK], rows=["Ring", "Ring"],
        mark_type_1="Pie", mark_type_2="Circle", dual_axis_shelf="rows",
        color_1="Slice", wedge_size_1="Slice Share", label_2="Track Share",
        size_value_1="2", size_value_2="1", mark_color_2="#ffffff", hide_axes=True,
        color_map_1={"Track":"#675493", "Other":"#eeeeee"})
    e.configure_chart("Bar-Participate", mark_type="Bar", rows=[FREQUENCY],
                      columns=["Participation Share"], label="Participation Share")
    filters = [{"column": "Question", "values": SENTIMENT},
               {"column": "Answer", "values": list(COLORS)}]
    e.configure_layered_chart("Bar-Diverging", rows=["Question"],
        columns=["Negative Share", "Positive Share"], axis_shelf="columns",
        fold_axes=True, synchronized=True, filters=filters,
        panes=[{"axis": "Negative Share", "mark_type": "Bar", "color": "Answer"},
               {"axis": "Positive Share", "mark_type": "Bar", "color": "Answer"}])
    e.configure_layered_chart("Bar-Vertical", columns=["Answer"],
        rows=["Question", "Answer Share"], filters=filters, axis_shelf="rows",
        panes=[{"axis":"Answer Share", "mark_type":"Bar", "color":"Answer", "label":"Answer Share", "detail":"MIN(Answer Order)"}],
        sort_descending="MIN(Answer Order)", sort_field="Answer", sort_mode="computed")
    e.configure_chart("Heatmap", mark_type="Square", columns=["Question"],
        rows=["Answer Rank"], detail="Answer", color="Answer Share", label="Answer Share",
        label_extra=["Answer"], mark_sizing_off=True, filters=[{"column": "Question", "values": CHOICES},
        {"column": "Answer", "exclude": True, "values": [None]}])
    for sheet in sheets:
        e.configure_worksheet_style(sheet, hide_gridlines=True, hide_borders=True,
            hide_table_dividers=True, hide_row_field_labels=True, hide_col_field_labels=True)
        e.set_window_state(sheet, hidden=False, zoom_entire_view=True)
    e.configure_worksheet_style("Bar-Participate", pane_mark_style={"mark-color": "#bdbdbd"})
    e.configure_worksheet_style("Donuts", hide_axes=True)
    e.configure_worksheet_style("Donuts", panes_style={1:{"mark_style":{"mark-labels-show":"false"}},2:{"mark_style":{"mark-color":"#ffffff", "size":"1"}}})
    for name, title in {"Donuts":"Which track do you participate in? — click to filter",
                        "Bar-Participate":"How often do you participate? — click to filter",
                        "Bar-Diverging":"Agreement with each statement",
                        "Bar-Vertical":"Response distribution",
                        "Heatmap":"What do you want more of? Rank your choices"}.items():
        e.set_worksheet_rich_title(name,[{"text":title,"fontsize":12}])
    def pos(x, y, w, h):
        return {"x": round(x/1400*100000), "y": round(y/1800*100000),
                "w": round(w/1400*100000), "h": round(h/1800*100000)}
    children = [{"type": "text", "runs": [{"text": "#WOW2021 | Survey responses", "font_size": 24, "bold": True}], "absolute": pos(20, 10, 1360, 80)}]
    for name, x, y, w, h in [("Donuts",20,100,660,280),("Bar-Participate",700,100,680,280),
                            ("Bar-Diverging",20,410,850,650),("Bar-Vertical",870,410,510,650),
                            ("Heatmap",20,1110,1360,660)]:
        children.append({"type": "worksheet", "name": name, "show_title": True,
                         "fit": "entire", "absolute": pos(x,y,w,h)})
    e.add_dashboard(DASHBOARD, width=1400, height=1800,
        layout={"type":"container", "direction":"floating", "children":children}, worksheet_names=sheets)
    for sheet, field in [("Donuts",TRACK),("Bar-Participate",FREQUENCY)]:
        for target in (s for s in sheets if s != sheet):
            e.add_dashboard_action(DASHBOARD, action_type="filter", source_sheet=sheet,
                target_sheet=target, field_mappings={field:field},
                caption=f"{sheet} filters {target}", clear_behavior="show-all")
    e.add_dashboard_action(DASHBOARD, action_type="highlight",
        source_sheets=["Bar-Diverging","Bar-Vertical"], target_sheets=["Bar-Diverging","Bar-Vertical"],
        fields=["Question","Answer"], event_type="on-hover", caption="Highlight sentiment")
    output = HERE / "outputs/replicated-workbook.twbx"
    output.parent.mkdir(exist_ok=True)
    e.save(str(output))
    return output


if __name__ == "__main__":
    print(build())
