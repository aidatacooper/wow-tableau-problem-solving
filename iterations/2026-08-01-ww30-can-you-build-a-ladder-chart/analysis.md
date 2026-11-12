# 2026-08-01 WW30 — tennis career ladder chart

The article builds a bump/ladder chart for Jannik Sinner's tournament rounds. Round Position maps Final through Round Robin to 1–11, Best Round per Date keeps the best round for each tournament, and a Grand Slam set plus boolean parameter controls whether only the four Grand Slams are shown. A winner calculation detects Sinner before the `d.` marker in Match text.

The extracted Hyper data contains tournament date, tournament, surface, round, rank, match, and score. The replica builds the Ladder and Match Details worksheets, including the parameter, set-like Grand Slam calculation, best-round filter, winner flag, and tooltips. The released cwtwb API supports the calculated fields and dashboard; no reusable SDK gap was required.

Acceptance scenarios:
- With pGrandSlamsOnly=true, only Australian Open, Roland Garros, Wimbledon, and US Open rows remain.
- Each tournament retains only its minimum Round Position (best achieved round).
- Is Winner is true for Match strings containing Sinner and false for opposing matches.

Native parameter toggling and hover events were not executed; the case remains functionally partial with acceptable visual delta.
