You are one GalaxyWiki GPT-5.5 extraction worker in [PROJECT_DIR].

You are part of a larger parallel run over astronomy papers.
Your job is to read exactly your assigned papers and write paper-galaxy evidence
rows for named galaxy-like objects that qualify under the output guide.

You are not alone in the codebase. Other workers may be writing their own batch
output directories at the same time. Do not revert, delete, rename, or modify
files outside your assigned batch output directory. If you notice unrelated
changes elsewhere, ignore them.

You may use shell tools, python3, and uv. Do not use git. Do not call external
model APIs. Do not use SIMBAD, NED, Sesame, VizieR, ADS, arXiv, web search, or
any external lookup. Do not download or stream tar shards. Use the assigned
SQLite database as your only source for paper text.

Assignment id: [ASSIGNMENT_ID]
Assigned paper ids, in required output order: [ASSIGNED_PAPER_IDS_JSON]
Assigned shards: [ASSIGNED_SHARDS_JSON]
Assigned batch output directory: [BATCH_OUTPUT_DIR]
Run directory: [RUN_DIR]
Full-text SQLite database: [FULL_TEXT_SQLITE]
Subagent output guide: [SUBAGENT_OUTPUT_GUIDE]
UAT allowlist: [UAT_TERMS_PATH]

Before extracting, read:
- [SUBAGENT_OUTPUT_GUIDE]
- [UAT_TERMS_PATH]
- [PROJECT_DIR]/notes/full_galaxywiki_prefilter_plan_2026-05-17.md

The prefilter intentionally excludes Milky-Way-only papers from GalaxyWiki. Do
not emit the Milky Way, the Galaxy, Galactic structure, Galactic disk, Galactic
halo, Galactic bulge, Galactic center, Galactic ISM, Galactic stellar
populations, or objects inside the Milky Way as GalaxyWiki galaxy rows.

Also reject Milky-Way fossil-record / Galactic-archaeology structures as
GalaxyWiki rows. Do not emit named stellar streams, halo substructures,
accreted debris clouds, inferred merger progenitors, or accretion-event labels
inside the Milky Way, such as Gaia Sausage/Enceladus, Sequoia, Thamnos, Helmi
streams, or similar objects, unless the paper is directly discussing a named
surviving non-Milky-Way galaxy.

Named non-Milky-Way galaxies may qualify when the paper directly discusses the
galaxy itself. This includes M31, M33, the Magellanic Clouds, named dwarf
galaxies, named AGN hosts, named lensed galaxies, high-redshift galaxy
candidates, merger remnants, and other galaxy-like objects, as defined by the
output guide.

Your task:

1. Query only your assigned papers from [FULL_TEXT_SQLITE].
2. Process papers in exactly the order listed in [ASSIGNED_PAPER_IDS_JSON].
3. For each paper, decide which named galaxy-like objects qualify under
   [SUBAGENT_OUTPUT_GUIDE].
4. Write exactly the files required by [SUBAGENT_OUTPUT_GUIDE] inside
   [BATCH_OUTPUT_DIR] only.
5. Validate your files before finishing.

The SQLite database has a `papers` table with at least these columns:

papers(
  paper_id TEXT PRIMARY KEY,
  shard TEXT NOT NULL,
  source_member TEXT NOT NULL,
  text_chars INTEGER,
  text_utf8_bytes INTEGER,
  full_text TEXT NOT NULL
)

It may include extra metadata columns from the manifest or Gemini triage. Ignore
extra columns unless useful for accounting. Query by paper_id using parameter
binding. Do not rely on the sqlite3 shell being installed; use Python's
standard sqlite3 module if needed.

Use a query shaped like:

SELECT
  paper_id,
  shard,
  source_member,
  text_chars,
  text_utf8_bytes,
  full_text
FROM papers
WHERE paper_id IN (...)

Then reorder the returned rows to match [ASSIGNED_PAPER_IDS_JSON].

Important extraction rules:

- Follow [SUBAGENT_OUTPUT_GUIDE] as the authority for acceptance rules, field
  names, output files, JSONL formatting, sentence counts, evidence quotes,
  summaries, discussion_extent, coordinates, paper_status rows, and
  run_summary.
- Emit paper-galaxy evidence rows only. Do not make final wiki pages.
- Do not deduplicate galaxies across papers.
- Do not canonicalize names using outside knowledge.
- Use the raw name exactly as the paper uses it.
- Include aliases only when the same paper explicitly states them.
- Include coordinates only when the paper explicitly states coordinates for
  that object.
- Use only exact UAT preferred labels from [UAT_TERMS_PATH].
- Keep evidence compact. If a paper discusses one galaxy throughout, choose
  representative evidence instead of quoting the whole paper.
- Do not emit more than 30 accepted galaxy rows for a single paper.
- Prefer precision over recall when the output guide is not satisfied.

Required output location:

Write all final batch files directly inside:

[BATCH_OUTPUT_DIR]

Do not write final files anywhere else. Temporary scratch files are allowed only
inside [BATCH_OUTPUT_DIR] and should be removed or clearly marked as temporary
before finishing.

Validation before finishing:

- Confirm the required output files exist.
- Confirm every JSONL line and run_summary.json parse as valid JSON.
- Confirm every assigned paper appears exactly once in paper_status.jsonl.
- Confirm no unassigned paper appears in outputs.jsonl or paper_status.jsonl.
- Confirm the main counts in paper_status.jsonl, outputs.jsonl, and
  run_summary.json agree.
- Do a quick sanity check that accepted rows follow [SUBAGENT_OUTPUT_GUIDE].

If a paper cannot be processed because text is missing, empty, or malformed,
write an error status for that paper rather than skipping it.

In your final reply, report:
- files written
- assigned paper count
- accepted, rejected, and error paper counts
- accepted paper-galaxy row count
- validation status
- any uncertainty or notable borderline decisions

# GalaxyWiki Subagent Output Guide

## Goal

Read each paper and output **paper-galaxy evidence rows**.

A row means:

> This paper directly discusses this named galaxy or galaxy-like object in at least 3 substantive prose sentences, and the row records the evidence.

Do not make final wiki pages.
Do not deduplicate galaxies across papers.
Do not canonicalize names using outside knowledge.
Do not use SIMBAD, NED, or external lookup.
Entity resolution happens later.

---

# Files to write

Each batch must write three files:

```text
outputs.jsonl
paper_status.jsonl
run_summary.json
```

`outputs.jsonl` contains one row per accepted paper-galaxy pair.

Do not write more than 30 `outputs.jsonl` rows for any single paper.

`paper_status.jsonl` contains exactly one row per processed paper, with status `accepted`, `rejected`, or `error`.

`run_summary.json` contains batch-level counts.

---

# Acceptance rule

Accept a galaxy only if all of the following are true:

1. The object is identified by a name, catalog/source designation, paper-local name, or explicit coordinates used as an object identifier.
2. The object is a galaxy or galaxy-like object.
3. The paper contains at least **3 direct prose sentences** about that object.
4. The paper contains exact evidence text that can support a concise summary of what the paper says about the object.

Reject table-only, bibliography-only, figure-label-only, sample-list-only, and generic population mentions with less than three sentences.

If more than 30 galaxy-like objects in one paper appear to qualify, emit at
most 30 rows for that paper. Choose the 30 best-supported and most substantively
discussed objects, prioritizing objects central to the paper over appendix,
atlas, or survey-description entries.

---

# What counts as a galaxy-like object?

Accept named objects such as:

```text
NGC 3923
M31
B2 0648+27
SDSS J...
WISEA J...
GN-z11
```

The object can be a galaxy, galaxy candidate, dwarf galaxy, radio galaxy, AGN host galaxy, interacting galaxy, merger remnant, high-redshift galaxy candidate, etc. This list is not comprehensive, use your own judgement.

The word “galaxy” does not need to appear in the object name.

---

# What does not count?

Reject:

```text
generic galaxy populations
host galaxies with no name, source designation, paper-local name, or coordinates used as an identifier
clusters or groups without individually discussed named galaxies
table-only catalog entries
bibliography-only mentions
figure-label-only mentions
sample membership only
pure simulations unless explicitly about real or observed named galaxies
non-galaxy objects only
```

A sentence like “NGC 3923 is in our sample” does not count as substantive discussion.

---

# Sentence counting rule

Use:

```json
"total_evidence_sentence_count": 3
```

This counts the number of direct galaxy-specific prose sentences in the selected evidence quotes.

It does not need to count every sentence in the whole paper.

If the whole paper is about one galaxy, choose a representative quote and set:

```json
"discussion_extent": "paper_focus"
```

---

# Evidence quote rule

Each accepted row may include 1–3 evidence quotes.

Each quote should contain 1–5 direct discussion sentences.

Across all evidence quotes, `total_evidence_sentence_count` must be between 3 and 8.

Never include more than 8 direct discussion sentences for one paper-galaxy row.

If you select 6–8 evidence sentences, split them across 2–3 quote objects.
Do not put 6 or more counted sentences in a single quote object.

If the paper contains more than 8 relevant sentences about the galaxy, choose the most representative evidence sentences rather than quoting everything.

---

# Summary rule

The summary should describe the main object-specific claims the paper makes about the galaxy.

Aim for 20–40 words.

Do not exceed 40 words.

The summary may be one sentence or two short sentences, but it should stay compact.

Every major claim in the summary must be supported by the evidence quotes.

---

# `outputs.jsonl`

Write one row per accepted paper-galaxy pair.

Example:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "150X_XXXXX",
  "source_member": "150X_XXXXX.json",

  "raw_name": "NGC XXXX",
  "aliases_in_paper": [],

  "summary": "The paper describes NGC XXXX as a disturbed post-merger galaxy, linking its blue shell knots, counter-rotating central disk, and metal-rich tidal plume to debris from a gas-rich dwarf accreted 1.2 Gyr ago.",

  "evidence_quotes": [
    {
      "quote": "Deep optical imaging reveals a system of asymmetric blue shell knots around NGC XXXX. The knots are concentrated along the eastern side of the galaxy and have colors consistent with a young stellar population superposed on older tidal debris.",
      "evidence_sentence_count": 2
    },
    {
      "quote": "Integral-field spectroscopy shows that the central stellar disk counter-rotates relative to the outer body of NGC XXXX. We also detect a faint tidal plume whose metallicity declines smoothly with radius, suggesting that the material originated in a gas-rich dwarf companion accreted roughly 1.2 Gyr ago.",
      "evidence_sentence_count": 2
    }
  ],

  "total_evidence_sentence_count": 4,
  "discussion_extent": "short_paragraph",

  "uat_terms": ["Galaxy interactions"],

  "paper_coordinates": {
    "ra": "06h52m02.50s",
    "dec": "+27d27m39.4s",
    "coordinate_text": "RA = 06h52m02.50s, Dec = +27d27m39.4s"
  }
}
```

---

# Field rules

## `raw_name`

Use the name exactly as the paper uses it.

Do not canonicalize.

Good:

```json
"raw_name": "B2 XXX+XX"
```

Do not replace it with another catalog name unless the paper itself uses that name.

## `aliases_in_paper`

Other names explicitly stated in the same paper.

Use `[]` if none.

## `evidence_quotes`

Each quote object must contain:

```json
{
  "quote": "Exact evidence sentences copied from full_text.",
  "evidence_sentence_count": 3
}
```

The quote must be exact paper text, with only minor whitespace normalization allowed.

The sentence count is the number of direct object-specific prose sentences inside that quote.

## `total_evidence_sentence_count`

Total number of direct discussion sentences across all evidence quotes.

Must be between 3 and 8 for accepted rows.

This must equal the sum of `evidence_sentence_count` across all evidence quotes.

This counts only the selected evidence quotes, not every sentence in the paper about the object.

If the paper contains more than 8 relevant sentences about the galaxy, choose the most representative evidence sentences rather than quoting everything.

## `discussion_extent`

Use one of:

```text
exactly_three_sentences
short_paragraph
multiple_paragraphs
section
paper_focus
unclear_but_qualifies
```

Use `paper_focus` when the paper is mainly or entirely about the galaxy.

## `uat_terms`

Use 0–5 relevant astronomy terms.

Examples:

```json
["Radio galaxies", "Galaxy mergers", "Tidal tails"]
```

Only include terms supported by the paper. These should come from uat_galaxy_terms.txt located at [LOCATION OF uat_galaxy_terms.txt].

Use only the exact preferred-label text before the tab in the allowlist. If no
exact supported term is present in the allowlist, use `[]` rather than inventing
a near match.

## `paper_coordinates`

Only include coordinates if stated in the paper, otherwise put as null.

Do not look them up.

If absent:

```json
"paper_coordinates": {
  "ra": null,
  "dec": null,
  "coordinate_text": null
}
```

---

# `paper_status.jsonl`

Write exactly one row per processed paper.

This file is for accounting and auditing. It should not duplicate the full galaxy evidence rows from `outputs.jsonl`.

## Accepted paper

If the paper has one or more accepted galaxy rows:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "accepted",
  "accepted_galaxy_row_count": 3,
  "rejection_reason": null
}
```

## Rejected paper

If the paper has no accepted galaxy rows:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "rejected",
  "accepted_galaxy_row_count": 0,
  "rejection_reason": "No named galaxy is discussed in three or more direct prose sentences."
}
```

## Error paper

If the paper cannot be processed:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "error",
  "accepted_galaxy_row_count": 0,
  "rejection_reason": "The paper text was missing, empty, or malformed."
}
```

Allowed `status` values:

```text
accepted
rejected
error
```

`rejection_reason` is a string with less than 10 words.

Use `null` for `rejection_reason` when `status` is `accepted`.

---

# `run_summary.json`

Write one object per batch.

```json
{
  "run_id": "20260517T041000Z",
  "batch_id": "batch-005X",

  "input_paper_count": 10,
  "processed_paper_count": 10,
  "accepted_paper_count": 9,
  "rejected_paper_count": 1,
  "error_paper_count": 0,
  "accepted_galaxy_row_count": 17
}
```

---

# JSONL rules

Every line in every `.jsonl` file must be valid JSON.

Do not include Markdown in JSONL files.

Do not include comments.

Do not include trailing commas.

Use double quotes for strings.

Use `null` for missing optional values.

Use `[]` for empty lists.

---

# Final checklist

Before outputting an accepted row, confirm:

```text
The object has a name, catalog/source designation, paper-local name, or coordinates used as an identifier.
The object is galaxy-like.
The paper has at least 3 direct prose sentences about it.
The paper has no more than 30 accepted galaxy rows.
The quote is exact paper text.
The summary states how the paper describes the galaxy.
The raw name is not canonicalized.
Coordinates are included only if stated in the paper.
The JSON is valid.
```
