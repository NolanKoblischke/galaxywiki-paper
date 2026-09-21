# Galaxy page summaries

The bundled summaries are saved Gemini outputs, not new inference. The original
generation used the then-current galaxy memberships; the submission uses the
saved corrected summaries and memberships after the false-Abell removals.

## Model and response settings

The regular generator used `gemini-3.5-flash` through the Google Gen AI client,
with temperature `0.1`, `thinking_level="minimal"`, response MIME type
`application/json`, and the response schema below. No seed was set. The same
configuration was used for the regular repair prompt. The regular script's
default is three validation attempts including the first generation; resumed
passes used larger limits for some remaining rows (up to five recorded attempts
for a final successful row). These are saved results, not a claim that a fresh
run will produce identical text.

```json
{
  "type": "OBJECT",
  "properties": {
    "summary": {
      "type": "STRING"
    }
  },
  "required": [
    "summary"
  ]
}
```

## Saved system, user, repair, and tail-fill prompts

The following is the archived prompt record, unchanged. Three one-source
entries used the shorter tail-fill prompt: UDG 13, UDG 15, and the host of
FRB 20210807D. Their saved model is also `gemini-3.5-flash`; separate per-request
tail-fill temperature/thinking settings are not recorded in this prompt record.

````markdown
# Entity Summary Generation Prompt

## System Prompt

You write objective, concise encyclopedia summaries for galaxy pages. Use only the supplied literature evidence. Do not invent facts, classifications, measurements, or causal claims. Every factual clause must be supported by source_id citations copied exactly from the evidence. Return JSON with only one key: summary.

## User Prompt Template

```text
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
```

## Repair Prompt Template

```text
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
```

## Evidence Capping

Generation is run with a fixed estimated prompt-token ceiling. Entities whose
full evidence JSON fits under the cap include all paper-level mention summaries
and all full evidence quote passages. Entities whose full evidence JSON exceeds
the cap use a deterministic source-order-spanning selection under the same
fixed prompt budget; selected sources retain their paper-level summaries and as
many full quote passages as fit. Summaries may only cite source IDs included in
the final Evidence JSON sent to the model.

## Tail-Fill Prompt Template

Three one-source entities timed out repeatedly through the async full-prompt
client path. They were generated with this minimal Gemini prompt shape, still
using the complete available mention summary and full quote passages for that
entity.

```text
Output JSON with only summary. Write exactly two objective sentences with square-bracket citations, using only this evidence.
Galaxy: {chosen_name}
Evidence summary: {paper_level_summary}
Full quote passages:
{full_quote_passages}
Citation source_id: {source_id}
Citation format must be [{source_id}], not parentheses.
```
````

## Evidence construction and selection

The input JSON contains `entity_id`, `chosen_name`, `aliases`, `ra_deg`,
`dec_deg`, `evidence_capped`, and `sources`. Each source is one mention and
contains `source_id = "arXiv:" + arxiv_id`, `mentioned_as` (the original name),
`paper_level_summary`, `uat_terms`, and `full_quotes` (nonempty quote strings).
Sources are ordered by total evidence sentence count descending, then paper ID
and mention ID ascending; quotes by `(mention_id, quote_index)`. Distinct
mentions can therefore have the same paper `source_id`.

The regular generator estimated tokens as characters / 1.5 and used a 20,000
token ceiling. It serialized JSON with `ensure_ascii=False` and
`separators=(",", ":")`. The evidence-character budget was
`max(1000, int(20000 * 1.5) - len(system_prompt) - len(user_prompt_with_empty_evidence))`.
When the complete JSON fit, all sources and full quotes were included.

Above the budget, selection first tried each source with no quotes in the
index order computed below. A source was added if its candidate payload fit;
the first source was kept even if it alone exceeded the budget. Then the same
index order was used to add full quotes from included sources, in quote order.
For each quote, the first selected source with its `source_id` received the
quote; if it did not fit, additions stopped for that source. This preserves
the generator's behavior even when two mentions share a paper ID. No quote
text was shortened. Capped payloads also include `capping_method` with this
exact value:

```text
Deterministic source-order-spanning selection under a fixed prompt budget; selected sources keep paper-level summaries and as many full quote passages as fit.
```

The source index order is deterministic and consumes no random seed:

```python
def interleaved_indices(size: int) -> list[int]:
    """Return a deterministic order that samples the source list broadly."""
    if size <= 0:
        return []
    seen: set[int] = set()
    order: list[int] = []
    queue: list[tuple[int, int]] = [(0, size - 1)]
    while queue:
        left, right = queue.pop(0)
        for index in (left, right, (left + right) // 2):
            if left <= index <= right and index not in seen:
                seen.add(index)
                order.append(index)
        if left + 1 < right:
            midpoint = (left + right) // 2
            queue.append((left + 1, midpoint))
            queue.append((midpoint + 1, right - 1))
    return order
```

## Response checks defining repair requests

Parsed output had to be an object with string `summary`; whitespace was
collapsed to single spaces. A regular response was sent to the repair prompt
when any of these conditions failed:

- At least one arXiv source ID is present and all parsed source IDs are among
  those in the final evidence payload.
- No square bracket contains more than two parsed source IDs.
- None of `remarkable`, `enormous`, `powerful`, `unusual`, `dramatic`, or
  `fascinating` appears as a whole word, case-insensitively.
- The sentence-ending punctuation count is exactly two.

The source-ID and sentence-count rules were:

```python
import re

SOURCE_ID_RE = re.compile(
    r"arXiv:(?:[a-z-]+/[0-9]{7}|[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)"
)
BRACKET_RE = re.compile(r"\[([^\]]+)\]")

def sentence_count(summary: str) -> int:
    without_brackets = BRACKET_RE.sub("", summary)
    without_brackets = re.sub(r"\b([A-Z])\.\s+(?=[A-Z])", r"\1 ", without_brackets)
    # Count likely sentence boundaries, not periods in coordinate labels such as
    # "R.A. 17h", object labels such as "ID. 93", or decimal values.
    return len(
        re.findall(
            r"(?<!\d)[.!?](?:\s+(?=[A-Z])|$)",
            without_brackets.strip(),
        )
    )
```

The next repair request contained the previous summary, each problem prefixed
with `"- "` and joined by a newline, and the same evidence JSON. Word limits and support for each
factual clause were prompt instructions, not programmatic semantic tests;
source-ID membership alone does not prove a citation supports a claim.
