# Coordinate resolution

The automatic NED pass was followed by GPT-5.5 workers over the remaining
mentions. The source extraction was kept separate from this coordinate overlay.
The released `data/coordinates.parquet` contains the saved, corrected result;
reproducing the submission does not make new catalog or model requests.

## Programmatic NED pass

Names were considered in raw-name order followed by aliases, preserving alias
order. Each recognized common name was queried directly; otherwise catalog
patterns were applied in the order below and matches in textual order. Duplicate
normalized queries were removed while preserving first occurrence. The first
candidate returning numeric coordinates was accepted, without a contextual
object-identity check. No source-paper coordinates were preferred in this pass.

The endpoint was
`https://ned.ipac.caltech.edu/NED::API/OverviewOfObject?TARGET=<URL-encoded query>`.
The parser read the first VOTable row and the `equ_j2000_lon` and
`equ_j2000_lat` fields as FK5 J2000 decimal degrees; it also saved the first
`CrossID_list` entry, `pretype`, `pos_reference`, and the query URL. Missing or
failed coordinates remained unresolved for the agents.

The historical Abell pattern below also matches bare `A` designations. Review
subsequently invalidated 112 false-Abell matches: final coordinates are null,
`has_resolved_coordinates` is false, and status is `rejected_false_abell`.
The saved attempt fields remain as evidence of the rejected lookup. Those
fields must not be used to restore invalidated coordinates. The corrected
membership excludes those 112 mentions; their extraction rows are retained.

These are the original matching and normalization rules, including that
historical pattern, rather than a revised resolver:

```python
import re
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class PatternDef:
    label: str
    regex: re.Pattern[str]


CATALOG_PATTERNS = [
    PatternDef("messier_m", re.compile(r"(?i)\b(?:M|Messier)\s*0*(\d{1,3})\b")),
    PatternDef("ngc", re.compile(r"(?i)\bNGC\s*0*(\d{1,5})(?:\s*[-/]\s*[A-Z0-9]+)?[A-Z]?\b")),
    PatternDef("ic", re.compile(r"(?i)\bIC\s*0*(\d{1,5})(?:\s*[-/]\s*[A-Z0-9]+)?\b")),
    PatternDef("ugc", re.compile(r"(?i)\bUGC\s*0*(\d{1,6})(?:\s*[-/]\s*[A-Z0-9]+)?\b")),
    PatternDef("pgc_leda", re.compile(r"(?i)\b(?:PGC|LEDA)\s*0*(\d{1,8})\b")),
    PatternDef("sdss", re.compile(r"(?i)\bSDSS\s*(?:J\s*)?[0-9]{4,6}[.+-][0-9]{4,7}\b")),
    PatternDef("2mass", re.compile(r"(?i)\b2MASS\s*(?:J\s*)?[A-Z0-9.+-]+")),
    PatternDef("wise", re.compile(r"(?i)\b(?:WISE|AllWISE|WISEA)\s*(?:J\s*)?[A-Z0-9.+-]+")),
    PatternDef("iras", re.compile(r"(?i)\bIRAS\s*F?\s*[0-9]{4,6}[+-][0-9]{3,6}\b")),
    PatternDef("first", re.compile(r"(?i)\bFIRST\s*(?:J\s*)?[0-9][A-Z0-9.+-]*")),
    PatternDef("nvss", re.compile(r"(?i)\bNVSS\s*(?:J\s*)?[0-9][A-Z0-9.+-]*")),
    PatternDef("3c_4c", re.compile(r"(?i)\b[34]C\s*[0-9]{1,4}(?:\.[0-9]+)?(?:[+-][0-9]+)?\b")),
    PatternDef("pks", re.compile(r"(?i)\bPKS\s*[0-9]{3,4}[+-][0-9]{2,4}\b")),
    PatternDef("mrk", re.compile(r"(?i)\b(?:Mrk|Markarian|Ark)\s*[0-9]{1,5}\b")),
    PatternDef("arp", re.compile(r"(?i)\bArp\s*[0-9]{1,4}(?:\s*[-/]\s*[A-Z0-9]+)?\b")),
    PatternDef("hcg", re.compile(r"(?i)\bHCG\s*[0-9]{1,4}[A-Z]?\b")),
    PatternDef("abell", re.compile(r"(?i)\b(?:Abell|A)\s*[0-9]{1,5}(?:\s*[-/]\s*[A-Z0-9]+)?\b")),
    PatternDef("macs", re.compile(r"(?i)\bMACS\s*J?[0-9][A-Z0-9.+-]*")),
    PatternDef("rxj", re.compile(r"(?i)\b(?:RX\s*J|RXJ|1RXS\s*J)[0-9][A-Z0-9.+-]*")),
    PatternDef("xmm", re.compile(r"(?i)\bXMM[SU]?L?\s*J?[0-9][A-Z0-9.+-]*")),
    PatternDef("chandra_cxo", re.compile(r"(?i)\b(?:CXO|Chandra)\s*J?[0-9][A-Z0-9.+-]*")),
    PatternDef("eso", re.compile(r"(?i)\bESO\s*[0-9]{1,4}\s*[-]\s*[0-9]{1,4}\b")),
    PatternDef("mcg", re.compile(r"(?i)\bMCG\s*[+-]?[0-9]{1,3}\s*[-]\s*[0-9]{1,3}\s*[-]\s*[0-9]{1,3}\b")),
    PatternDef("vcc", re.compile(r"(?i)\bVCC\s*[0-9]{1,5}\b")),
    PatternDef("fcc", re.compile(r"(?i)\bFCC\s*[0-9]{1,5}\b")),
    PatternDef("ddo", re.compile(r"(?i)\bDDO\s*[0-9]{1,5}\b")),
]


COMMON_NAME_PATTERN = re.compile(
    r"(?i)^\s*(?:"
    r"M31|M32|M33|M51|M81|M82|M87|M101|"
    r"LMC|SMC|"
    r"Large Magellanic Cloud|Small Magellanic Cloud|"
    r"Centaurus\s+A|Circinus(?:\s+galaxy)?|"
    r"Andromeda(?:\s+Galaxy| \s+galaxy)?|"
    r"Triangulum(?:\s+Galaxy| \s+galaxy)?|"
    r"Fornax(?:\s+dSph)?|Sculptor(?:\s+dSph)?|"
    r"Cygnus\s+A|Pictor\s+A|Hercules\s+A|Virgo\s+A|Fornax\s+A|"
    r"Antennae(?:\s+Galaxies|\s+galaxies)?|"
    r"BL\s+Lac(?:ertae)?|OJ\s*287"
    r")\s*$"
)

def normalize_space(value: Any) -> str:
    return " ".join(str(value or "").split())

def normalize_query(value: str) -> str:
    value = normalize_space(value)
    value = re.sub(r"\s*([+-])\s*", r"\1", value)
    value = re.sub(r"\s*/\s*", "/", value)
    value = re.sub(r"\s*-\s*", "-", value)
    value = re.sub(r"(?i)^(NGC|IC|UGC|PGC|LEDA|VCC|FCC|DDO)([0-9])", r"\1 \2", value)
    value = re.sub(r"(?i)^(Mrk|Markarian|Ark|Arp|HCG|Abell|ESO|MCG|VCC|FCC|DDO)([0-9+-])", r"\1 \2", value)
    value = re.sub(r"(?i)^M\s+([0-9])", r"M\1", value)
    return value.strip(" ,.;:")

def source_names(row: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    raw = normalize_space(row.get("raw_name"))
    if raw:
        out.append(("raw_name", raw))
    for alias in row.get("aliases_in_paper") or []:
        value = normalize_space(alias)
        if value and ("alias", value) not in out:
            out.append(("alias", value))
    return out

def candidate_queries(row: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for source_field, source_value in source_names(row):
        if COMMON_NAME_PATTERN.fullmatch(source_value):
            query = normalize_query(source_value)
            if query and query not in seen:
                seen.add(query)
                candidates.append(
                    {
                        "query": query,
                        "source_field": source_field,
                        "source_value": source_value,
                        "pattern": "common",
                    }
                )
            continue
        for pattern in CATALOG_PATTERNS:
            for match in pattern.regex.finditer(source_value):
                query = normalize_query(match.group(0))
                if query and query not in seen:
                    seen.add(query)
                    candidates.append(
                        {
                            "query": query,
                            "source_field": source_field,
                            "source_value": source_value,
                            "pattern": pattern.label,
                        }
                    )
    return candidates
```

## Coordinate agents

Workers used `gpt-5.5` in Codex, with `reasoning_effort="medium"` requested by
the recorded orchestrator instructions. Each batch contained up to five papers,
and every unresolved mention for those papers was supplied. The saved run
contained 1,817 batches over 9,084 papers and 20,562 mentions. Temperature and
seed are not specified in the archived assets. Workers could inspect local
full text, then use NED and other primary or curated astronomy sources. The
frozen worker prompt and JSON response schema follow unchanged. References to
workspace files in the prompt are historical; the NED contract needed to
understand the lookup is stated above.

## Historical worker prompt

````markdown
# GalaxyWiki Coordinate Resolution Subagent Prompt

You are one coordinate-resolution worker for GalaxyWiki.

You are given up to 5 papers from the combined GalaxyWiki dataset, with the
unresolved `galaxy_mentions` for those papers. Your job is to find the best
J2000 sky coordinates for each unresolved mention using the paper context, NED,
and other reliable astronomy sources when needed.

You are working on a shared server with other users and other workers. Be
resource-conscious: do not download large datasets or files. If you absolutely have to download temporary files, keep them small and
inside your assigned batch directory. Avoid high-concurrency web requests.

Write exactly one JSON object per assigned unresolved mention to
`outputs.jsonl`, one object per line. Return rows in the same order as the
input records. Do not skip mentions. If you cannot resolve a mention, write an
explicit unresolved row.

## Source Of Truth And Scope

The target object is the `galaxy_mention`, not merely a name string. Use
`mention_id` as the primary key.

The provided fields are a starting place for you to figure out the object's RA and Dec:

- `mention_id`
- `paper_id`
- `arxiv_id`
- `arxiv_url`
- `raw_name`
- `aliases_in_paper`
- `summary`
- `evidence_quotes`
- `paper_coordinates`
- `programmatic_ned_result`

We want the coordinates for the exact object discussed in the paper. Some names are
paper-local labels such as `G1`, `source A`, `host galaxy`, or `object 3`.
Never accept a NED result for such a generic label by name alone.
Generic labels require paper context, paper coordinates, a table, figure
caption, or a reliable source that ties the local label to an absolute object
or position.

The original GalaxyWiki extraction is immutable. You are creating an external
coordinate-resolution overlay.

## Allowed Sources

Use these sources, in roughly this order:

1. The source arXiv paper, especially coordinates in text, tables, captions, or
   object-identification sections.
2. NED, using the API documented in `notes/ned_api_specification.md`.
3. Web Search: Other papers, journal pages, catalog papers, survey pages, SIMBAD, or other primary/curated
   astronomy sources when the paper and NED are insufficient. Use your judgement!

## Local Paper Text

Use the local SQLite paper-text database first. Do not fetch arXiv or stream tar
shards just to read the paper text unless local text is missing or
insufficient.

The coordinate-resolution run-local text database is:

```text
results/galaxywiki_hf_version/coordinate_subagent_resolution/target_text.sqlite
```

It contains all 87,899 GalaxyWiki candidate papers.
The `papers` table is keyed by `paper_id`:

```sql
SELECT full_text
FROM papers
WHERE paper_id = ?
```

Use Python's standard `sqlite3` module; do not rely on the `sqlite3` shell being
installed. Example:

```python
import sqlite3

db = "results/galaxywiki_hf_version/coordinate_subagent_resolution/target_text.sqlite"

def load_paper_text(paper_id):
    with sqlite3.connect(db) as con:
        row = con.execute(
            "SELECT full_text FROM papers WHERE paper_id = ?",
            (paper_id,),
        ).fetchone()
    return row[0] if row else None
```

Search within the local text for the `raw_name`, aliases, nearby coordinate
phrases, table/caption mentions, and object-identification sections. The
provided evidence quotes are useful entry points, but the full local paper text
is available when more context is needed.

## Resolution Rules

Return `resolved_from_paper` when the paper itself gives coordinates for the
specific mention.

Return `resolved_from_ned` when NED resolves a non-generic raw name or alias
and the NED object is plausibly the object discussed in the paper.

Return `resolved_from_other_source` only when a reliable astronomy source gives
coordinates and NED is absent, ambiguous, or insufficient.

Return `unresolved_after_best_effort` when no absolute coordinates can be
verified. This is a safe call. The worst case scenario is that we assign an RA, Dec that doesn't actually match this object.

## NED Guidance

For NED API lookups, prefer:

```text
https://ned.ipac.caltech.edu/NED::API/OverviewOfObject?TARGET=<query>
```

Use the `Lon (Equatorial J2000)` and `Lat (Equatorial J2000)` degree fields
when available. Record the exact query in `ned_queries_attempted`.

If the programmatic NED pass already failed, inspect
`programmatic_ned_result` before retrying. Retry with reasonable spelling,
spacing, punctuation, and alias variants only when paper context supports the
variant.

Examples:

- `NGC1052-DF4` may need `NGC 1052-DF4` or another paper-supported form.
- `Antennae` may need paper context to decide whether the coordinate should be
  `NGC 4038`, `NGC 4039`, the pair, or unresolved/ambiguous.
- `Galaxy A` must not be resolved by direct `Galaxy A` lookup, since this is a paper local name. NED will not help you and should be avoided for paper-only names.

## Output Contract

Write `outputs.jsonl` only. It must contain exactly one JSON line for each
assigned unresolved mention in `assigned_mentions`.

Each line must validate against `subagent_output_schema.json`.

Use decimal degrees for `resolved_ra_deg` and `resolved_dec_deg`. RA must be in
`[0, 360]`; Dec must be in `[-90, 90]`.

Include concise but sufficient provenance:

- `source_urls`: URLs used to justify the coordinate, including NED/API URLs
  when used.
- `evidence`: short snippets or field names showing why the coordinate belongs
  to this mention.
- `method`: a brief explanation of how you connected the mention to the
  coordinate.

If unresolved, set coordinate fields to null and give a concrete
`reason_if_null`. When in doubt, leave unresolved!

## Required Final Checks

Before finishing:

- Confirm the number of output rows equals the number of assigned unresolved
  mentions.
- Confirm every input `mention_id` appears exactly once.
- Confirm output order matches input order.
- Confirm every resolved row has numeric RA/Dec degrees in range.
- Confirm every unresolved/ambiguous row has `reason_if_null`.
- Confirm generic paper-local names were not resolved by direct resolver lookup
  alone.
````

## JSON response schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GalaxyWiki coordinate-resolution subagent output row",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "mention_id",
    "paper_id",
    "raw_name",
    "aliases_in_paper",
    "resolved_ra_deg",
    "resolved_dec_deg",
    "coordinate_system",
    "resolution_status",
    "confidence",
    "coordinate_source",
    "resolved_name",
    "ned_queries_attempted",
    "ned_object_name",
    "source_urls",
    "evidence",
    "method",
    "reason_if_null"
  ],
  "properties": {
    "mention_id": {
      "type": "string",
      "minLength": 1
    },
    "paper_id": {
      "type": "string",
      "minLength": 1
    },
    "raw_name": {
      "type": "string",
      "minLength": 1
    },
    "aliases_in_paper": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "resolved_ra_deg": {
      "type": ["number", "null"],
      "minimum": 0,
      "maximum": 360
    },
    "resolved_dec_deg": {
      "type": ["number", "null"],
      "minimum": -90,
      "maximum": 90
    },
    "coordinate_system": {
      "type": ["string", "null"],
      "enum": ["FK5 J2000", "ICRS", null]
    },
    "resolution_status": {
      "type": "string",
      "enum": [
        "resolved_from_paper",
        "resolved_from_ned",
        "resolved_from_other_source",
        "ambiguous",
        "unresolved_after_best_effort"
      ]
    },
    "confidence": {
      "type": "string",
      "enum": ["high", "medium", "low", "none"]
    },
    "coordinate_source": {
      "type": ["string", "null"],
      "enum": ["paper", "ned", "paper_and_ned", "other_source", null]
    },
    "resolved_name": {
      "type": ["string", "null"],
      "description": "Best resolved object name or catalog designation, if any."
    },
    "ned_queries_attempted": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["query", "status", "url"],
        "properties": {
          "query": {
            "type": "string",
            "minLength": 1
          },
          "status": {
            "type": "string",
            "enum": ["resolved", "no_rows", "ambiguous", "not_applicable", "error"]
          },
          "url": {
            "type": ["string", "null"]
          },
          "note": {
            "type": ["string", "null"]
          }
        }
      }
    },
    "ned_object_name": {
      "type": ["string", "null"],
      "description": "NED standard/cross-ID object name used for the accepted coordinate, if any."
    },
    "source_urls": {
      "type": "array",
      "minItems": 0,
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "evidence": {
      "type": "array",
      "description": "Brief evidence strings, table references, API field names, or short snippets supporting the decision.",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "method": {
      "type": ["string", "null"],
      "description": "Short explanation of how the coordinate was chosen."
    },
    "reason_if_null": {
      "type": ["string", "null"],
      "description": "Required for ambiguous or unresolved rows; null for resolved rows."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "resolution_status": {
            "enum": [
              "resolved_from_paper",
              "resolved_from_ned",
              "resolved_from_other_source"
            ]
          }
        }
      },
      "then": {
        "required": ["resolved_ra_deg", "resolved_dec_deg", "coordinate_system"],
        "properties": {
          "resolved_ra_deg": {
            "type": "number"
          },
          "resolved_dec_deg": {
            "type": "number"
          },
          "coordinate_system": {
            "type": "string"
          },
          "reason_if_null": {
            "type": "null"
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "resolution_status": {
            "enum": ["ambiguous", "unresolved_after_best_effort"]
          }
        }
      },
      "then": {
        "properties": {
          "resolved_ra_deg": {
            "type": "null"
          },
          "resolved_dec_deg": {
            "type": "null"
          },
          "coordinate_system": {
            "type": "null"
          },
          "confidence": {
            "enum": ["low", "none"]
          },
          "reason_if_null": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  ]
}
```
