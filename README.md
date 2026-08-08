# WoW Tableau Problem-Solving Lab

An open, AI-assisted laboratory for understanding and rebuilding Workout
Wednesday Tableau cases with `cwtwb`.

Functional correctness is the primary goal. Interaction correctness and a
repeatable build come next; pixel-level visual parity is optional unless a
visual difference changes the answer or makes the workbook unusable.

“Training” in this repository means improving the case workflow, skills, and
tools through evidence from real cases. It does not mean model fine-tuning.

## Contribution loop

```text
Claim one post in a GitHub issue
-> use AI to analyze the post and author workbook
-> extract packaged data once and record its hashes
-> create an independent project under iterations/
-> rebuild and verify it with the released cwtwb package
-> submit a replicated, partial, or blocked PR
-> open a separate cwtwb issue/PR only for a confirmed reusable gap
```

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Agents also read [AGENTS.md](AGENTS.md).
The complete protocol is in
[`docs/protocols/community-case-contribution-v1.md`](docs/protocols/community-case-contribution-v1.md).

## Prepare and validate a case

```bash
python -m pip install -r requirements.txt
python scripts/prepare_case.py \
  --source path/to/author.twbx \
  --iteration-id YYYY-MM-DD-short-slug \
  --case-id stable-case-id \
  --post posts/YYYY-MM-DD-article.html

python scripts/validate_iteration.py iterations/<iteration-id>
python -m unittest discover -s tests -v
```

The preparation command extracts supported packaged data files into `inputs/`
and writes `inputs/source-lock.json`. It never copies the author's workbook.
After analysis, the builder may read extracted inputs, the written analysis,
blank templates, and cwtwb, but it must not reopen the author TWB/TWBX.

## Refresh the source archive incrementally

Use one command to discover new blog posts, rebuild the Tableau Public link
map, and download only missing workbooks or views:

```bash
python download_all.py --refresh
```

The incremental behavior uses stable identities:

- Posts are identified by canonical article URL, not by title or filename.
- A changed title reuses the existing local file instead of creating a copy.
- Limited crawls preserve older entries that were not revisited.
- Tableau workbooks and PNG views are skipped when their existing files are
  non-empty.
- A newly discovered view is downloaded even when its workbook already exists.

For rate-limited runs:

```bash
python download_all.py --refresh --max-items 25 --workers 1 --delay 1.2
```

`crawler.py` can also be run alone. `gen_links_map.py` then regenerates the
JSON, CSV, and Markdown link-map outputs from all local posts.

## Repository layout

```text
.github/                 Issue, PR, and CI configuration
docs/protocols/          Case contribution protocols
iterations/_template/    Starting point for a new case
iterations/<case>/       Analysis, builder, verifier, inputs, and outputs
scripts/prepare_case.py  Extract source data and create a case project
scripts/validate_iteration.py
                         Enforce provenance and run case validation
posts/                   Downloaded article HTML (generated, ignored)
dashboards/              Downloaded TWBX/PNG assets (generated, ignored)
usage/                   Shared case-consumption index
```

The main source tools are:

- `crawler.py`: incrementally archive WordPress posts.
- `gen_links_map.py`: extract and normalize Tableau Public links.
- `download_all.py`: primary resumable HTTP downloader.
- `build_dataset.py`: build the normalized, hash-verified dataset.
- `download_dashboards.py`: browser-based screenshot fallback.

## Publishing this lab as a standalone repository

This directory contains the repository-level README, dependencies, agent rules,
contribution guide, templates, and CI needed for a standalone project. To retain
its history from the parent `backup` repository:

```bash
git subtree split \
  --prefix=labs/wow-tableau-problem-solving \
  -b cwtwb-wow-lab
```

Before publishing, choose a license and review redistribution rights for posts,
author workbooks, and extracted data. When redistribution is not permitted,
commit URLs, hashes, and acquisition scripts instead of the original assets.

## Scope and known limits

- The source site is WordPress.com; the crawler reads public archive HTML with
  `urllib` and stops at the pagination boundary.
- Tableau Public links occur in both modern `/app/profile/.../viz/WB/VIEW` and
  legacy `#!/vizhome/WB/VIEW` forms; the link generator supports both.
- Tableau preview PNG endpoints may return a generic placeholder. Such images
  are evidence of acquisition only, not a visual acceptance baseline.
- `usage/consumed-cases.json` is the tracked source of truth for claimed cases.
  Research status and replication status remain separate fields.
- Author links are classified conservatively. Uncertain ownership remains
  marked for manual review.

Historical protocol drafts and iteration notes remain useful evidence, but the
community protocol above is the current contribution contract.
