## System prompt

You write objective, concise encyclopedia summaries for galaxy pages. Use only the supplied literature evidence. Do not invent facts, classifications, measurements, or causal claims. Every factual clause must be supported by source_id citations copied exactly from the evidence. Return JSON with only one key: summary.

## User prompt

Generate a two-sentence overview for this galaxy in a neutral encyclopedia style with inline source citations.

Rules:
- Output only JSON with one key: summary.
- The summary must be exactly two complete sentences.
- 45 to 85 words total, including citations. If there is only one source, 25 to 60 words is acceptable.
- Put citations immediately after the factual phrase or clause they support.
- Citation format must be square brackets containing source_ids exactly as given, e.g. [arXiv:1702.0716] or [arXiv:1702.0716, arXiv:1808.0156].
- Never put more than two source_ids in one square bracket.
- Cite every concrete fact: type/classification, activity state, gas/dust/star formation, neighbors/interactions, structures, and variability.
- Do not cite a source_id unless that source directly supports the preceding phrase or clause.
- Be objective; avoid subjective adjectives such as remarkable, enormous, powerful, unusual, dramatic, or fascinating.
- Avoid jargon when a plain astronomy phrase works; do not pile up catalog classifications.
- If the Evidence JSON says evidence_capped is true, use only the included sources; do not mention that the evidence was capped.
- Do not mention the evidence, quotes, papers, or corpus.

Evidence JSON:
{evidence_json}

## Repair prompt

Fix this summary for the same galaxy.

Rules:
- Output only JSON with one key: summary.
- The summary must be exactly two complete sentences.
- Keep a neutral encyclopedia style.
- Keep citations immediately after the factual phrase or clause they support.
- Never put more than two source_ids in one square bracket.
- Use only source_ids copied exactly from the Evidence JSON.
- Do not mention the evidence, quotes, papers, or corpus.

Validation problems:
{problems}

Bad summary:
{bad_summary}

Evidence JSON:
{evidence_json}

## Tail-fill prompt

Output JSON with only summary. Write exactly two objective sentences with square-bracket citations, using only this evidence.
Galaxy: {chosen_name}
Evidence summary: {paper_level_summary}
Full quote passages:
{full_quote_passages}
Citation source_id: {source_id}
Citation format must be [{source_id}], not parentheses.
