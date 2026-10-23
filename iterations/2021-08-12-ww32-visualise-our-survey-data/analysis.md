# Survey responses: participation, sentiment, and requested topics

The question is how the WoW community participates, how respondents judge the
challenges, and which subjects they want more of. The source is Donna Coles's
2021-08-12 article and the official 2021 Week 32 challenge (2021-08-11).

Analysis inspected the author's packaged workbook, which contains five sheets
and one Hyper extract. The builder starts from an empty workbook and reads only
the extracted survey data. It must never read the reference TWB/TWBX.

## Data and calculations

The extract has Respondent, Which track do you participate in?, How Often Do You
Participate, Question, and Answer. One respondent has multiple question rows:
all counts must use COUNTD(Respondent), never raw row counts.

- Donuts: track count / total unique respondents, and its complement; a white
  circle overlays each pie and labels its track and percentage.
- Participation: distinct respondent counts by frequency divided by the total.
- Sentiment: five questions; exclude N/A. Agree and Strongly Agree go right,
  Disagree and Strongly Disagree left. Half of neutral goes on each side.
  Percentages are partitioned by Question and addressed by Answer.
- Vertical bars: the same five questions with response percentages by Answer.
- Heatmap: the seven ranked-choice questions, excluding null answers. Rank
  counts uniquely within each question; label Answer and its percentage.

The sentiment questions are: I enjoy learning about new features; I want more
cross-over with other software and/or platforms; The challenges are too
difficult; The challenges are too easy; The challenges help me at work/school.
The seven choice questions have the exact prefix
`What do you want more of?  (Rank Your Choices)` with ordinal suffixes 1st–7th.

## Interaction contracts

Selecting a track filters the other four sheets; selecting participation
filters the other four sheets. Clearing selections restores all responses.
Hover highlighting links the sentiment and vertical bars by Question/Answer.
Counts and table calculations must recompute after filters, including
intersections of track and participation.

## Acceptance

Verify distinct-count oracles from the locked raw extract for unfiltered and
filtered populations; neutral halves sum to the full neutral percentage;
response percentages sum to 1 for each included question; requested topics
rank within their question. Check native table calculation addressing and
dashboard action field mappings. Desktop must load the generated workbook;
Cloud data/render comparison is required before marking replicated.
