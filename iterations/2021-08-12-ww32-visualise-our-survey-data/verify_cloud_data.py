"""Compare every replica worksheet export with the independent raw-data oracle."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from verify_replication import verify

HERE = Path(__file__).resolve().parent

def check():
    oracle = verify()['states']
    manifest = json.loads((HERE/'evidence/replica-data-exports.json').read_text(encoding='utf-8'))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert manifest['artifact_sha256'] == digest(HERE/'outputs/replicated-workbook.twbx')
    checked = 0
    def percentage(text, expected):
        nonlocal checked
        assert text.endswith('%'), text
        assert abs(float(text[:-1])/100-expected) <= 0.00500001, (text, expected)
        checked += 1
    for export in manifest['exports']:
        path = HERE/export['path']
        assert digest(path) == export['sha256']
        rows = list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
        assert rows, export
        state = oracle[{'default':'default','tableau':'Tableau','pbi':'PBI'}[export['state']]]
        view = export['view']
        if view == 'Donuts':
            data = [r for r in rows if r.get('Track Share')]
            assert len(data) == len(state['tracks'])
            for r in data:
                percentage(r['Track Share'],state['tracks'][r['Which track do you participate in?']]/state['respondents'])
        elif view == 'Bar-Participate':
            assert len(rows) == len(state['frequencies'])
            for r in rows:
                percentage(r['Participation Share'],state['frequencies'][r['How Often Do You Participate']]/state['respondents'])
        else:
            ranks = defaultdict(list)
            seen = set()
            for r in rows:
                q,a = r['Question'],r['Answer']
                if a not in state['questions'][q]['shares']:
                    # Tableau completes the answer domain for a pane even
                    # when that question has no respondents in the category.
                    assert view == 'Bar-Vertical' and not r['Answer Share'], r
                    continue
                expected = state['questions'][q]['shares'][a]
                seen.add((q,a))
                if view == 'Bar-Diverging':
                    neg = -expected if a in ('Disagree','Strongly Disagree') else -expected/2 if a == 'Neither Agree nor Disagree' else None
                    pos = expected if a in ('Agree','Strongly Agree') else expected/2 if a == 'Neither Agree nor Disagree' else None
                    for name,value in [('Negative Share',neg),('Positive Share',pos)]:
                        if value is None:
                            assert not r[name]
                        else:
                            percentage(r[name],value)
                else:
                    percentage(r['Answer Share'],expected)
                if view == 'Heatmap':
                    ranks[q].append((int(r['Answer Rank']),state['questions'][q]['counts'][a]))
            expected_questions = [q for q in state['questions'] if (q.startswith('What do you want more of?') if view=='Heatmap' else q in ('I enjoy learning about new features','I want more cross-over with other software and/or platforms','The challenges are too difficult','The challenges are too easy','The challenges help me at work/school'))]
            expected_marks = {(q,a) for q in expected_questions for a in state['questions'][q]['shares']}
            assert seen == expected_marks, (view,seen ^ expected_marks)
            for q,values in ranks.items():
                values.sort()
                assert [r for r,c in values] == list(range(1,len(values)+1))
                assert [c for r,c in values] == sorted((c for r,c in values),reverse=True)
    assert len(manifest['exports']) == 15
    result = {'result':'PASS','exports':15,'states':3,'percentage_checks':checked,
              'tolerance':'0.5 percentage points, because Tableau exports whole percentage labels',
              'artifact_sha256':manifest['artifact_sha256'],
              'scope':'All five replica sheets against raw-data oracle in default/Tableau/PBI states; original author dashboard compared visually, hidden author sheets were not modified or exported.'}
    (HERE/'evidence/cloud-data-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    check()
