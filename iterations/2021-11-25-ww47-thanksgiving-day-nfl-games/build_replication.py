"""Blank-workbook build; raw Hyper is the only business-data input."""
from pathlib import Path
from collections import defaultdict
from datetime import date
from tableauhyperapi import HyperProcess, Connection, Telemetry, TableDefinition, TableName, SqlType, CreateMode, Inserter
from cwtwb import TWBEditor
HERE=Path(__file__).resolve().parent

def prepare_rows(raw):
    teams=defaultdict(list)
    for day,away,a,home,h in raw: teams[home].append((date.fromisoformat(str(day)),away,int(a),int(h)))
    result=[]
    for home,games in sorted(teams.items()):
        games.sort(); wins=sum(h>a for _,_,a,h in games); losses=sum(h<a for _,_,a,h in games)
        record=f'{wins}-{losses}-{len(games)-wins-losses}'
        byyear={d.year:(d,v,a,h) for d,v,a,h in games}
        assert len(byyear)==len(games), 'Expected at most one Thanksgiving home game per year'
        cumulative=0
        for year in range(min(byyear),max(byyear)+1):
            item=byyear.get(year)
            if item:
                day,away,a,h=item; delta=(h>a)-(h<a); cumulative+=delta
                tip=f'{day}: {home} {"won" if delta>0 else "lost" if delta<0 else "tied"} vs {away}, {max(h,a)}–{min(h,a)}'
                identity=f'{day}|{home}|{away}'
            else:
                day=date(year,11,1); away=''; a=h=None; identity=''; tip=f'{year}: {home} did not host a game'
            result.append([year,home,day,away,h,a,identity,str(len(games)),record,f'{wins/len(games):.0%}',cumulative,tip])
    return result

def build():
    out=HERE/'outputs'; out.mkdir(exist_ok=True)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint,str(HERE/'inputs/NFL Thanksgiving Games.hyper')) as c:
            raw=c.execute_list_query('SELECT "Game Date","Visiting Team","Visiting Score","Home Team","Home Score" FROM "Extract"."Extract"')
        columns=[('Year',SqlType.int()),('Home Team',SqlType.text()),('Game Date',SqlType.date()),('Visiting Team',SqlType.text()),('Home Score',SqlType.int()),('Visiting Score',SqlType.int()),('Game Identity',SqlType.text()),('Total Games',SqlType.text()),('W-L-T',SqlType.text()),('Win %',SqlType.text()),('Cumulative Differential',SqlType.int()),('Game Tooltip',SqlType.text())]
        with Connection(hp.endpoint,str(out/'chart-data.hyper'),CreateMode.CREATE_AND_REPLACE) as c:
            c.catalog.create_schema('Extract'); table=TableDefinition(TableName('Extract','Extract'),[TableDefinition.Column(n,t) for n,t in columns]); c.catalog.create_table(table)
            with Inserter(c,table) as i: i.add_rows(prepare_rows(raw)); i.execute()
    e=TWBEditor(''); e.set_hyper_connection(str(out/'chart-data.hyper'),table_name='Extract')
    e.add_calculated_field('Result','IF ISNULL([Home Score]) THEN NULL ELSEIF [Home Score]>[Visiting Score] THEN 1.0 ELSEIF [Home Score]<[Visiting Score] THEN -1.0 ELSE 0.0 END',datatype='real')
    e.add_calculated_field('Score Difference','[Home Score]-[Visiting Score]',datatype='integer')
    e.set_field_format('Result','*"Win";"Loss";"Tie"')
    headers=['Home Team','Total Games','W-L-T','Win %']
    e.add_worksheet('Game Results')
    e.configure_layered_chart('Game Results',columns=['YEARTRUNC(Game Date)'],
        rows=headers+['SUM(Result)','SUM(Result)','SUM(Cumulative Differential)'],
        fold_axes=False, panes=[
            {'axis':'SUM(Result)','mark_type':'Bar','detail':'Game Identity',
             'tooltip':['Game Tooltip'],'mark_sizing_off':True,
             'mark_style':{'mark-color':'#777777','size':'0.01'}},
            {'axis':'SUM(Result)','mark_type':'Circle','detail':'Game Identity',
             'color':'SUM(Score Difference)','tooltip':['Game Tooltip'],
             'mark_sizing_off':True,'mark_style':{'size':'1.42'}},
            {'axis':'SUM(Cumulative Differential)','mark_type':'Area',
             'tooltip':['Home Team','Year','SUM(Cumulative Differential)'],
             'mark_style':{'mark-color':'#3d78a8'}}])
    e.configure_worksheet_style('Game Results',axis_style={'encodings':[
        {'field':'SUM(Result)','class':'1','scope':'rows','fold':True,'synchronized':True}],
        'per_field':[{'field':'SUM(Result)','class':'1','scope':'rows','attr':'display','value':'false'}]},
        color_style={'field':'SUM(Score Difference)','palette':'orange-blue-diverging','center':0})
    for pane in (0,1):
        e.configure_custom_tooltip('Game Results',[{'field':'ATTR(Game Tooltip)'}],pane_index=pane)
    e.configure_custom_tooltip('Game Results',[{'field':'Home Team'},{'text':' — '},
        {'field':'ATTR(Year)'},{'text':': cumulative wins minus losses '},
        {'field':'SUM(Cumulative Differential)'}],pane_index=2)
    e.add_dashboard('Thanksgiving NFL Games',width=1200,height=800,
        layout={'type':'container','direction':'vertical','children':[
            {'type':'text','text':'Thanksgiving Day NFL Games','font_size':'20','bold':True,'fixed_size':38},
            {'type':'text','text':'Home-team result: Win +1 | Tie 0 | Loss -1. Dot color: home score minus visiting score.',
             'font_size':'10','fixed_size':26},
            {'type':'color','worksheet':'Game Results','field':'SUM(Score Difference)',
             'pane_index':2,'caption':'Score Difference','mode':'horz','fixed_size':60},
            {'type':'worksheet','name':'Game Results','show_title':False,'weight':1}]})
    p=out/'replicated-workbook.twbx'; e.save(p); return p
if __name__=='__main__': print(build())

