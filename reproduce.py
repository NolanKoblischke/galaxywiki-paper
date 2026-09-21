# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "astropy==8.0.1",
#   "numpy==2.5.3",
#   "pandas==3.0.5",
#   "pyarrow==25.0.1",
#   "scipy==1.18.1",
# ]
# ///
"""Recompute coordinate groups and summarize the saved experiment and evaluations."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Iterable

import astropy.units as u
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from astropy.coordinates import SkyCoord, search_around_sky

ROOT = Path(__file__).resolve().parent
MATCH_RADIUS_ARCSEC = 1.0


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"['`'’]", "", text)
    text = re.sub(r"[^a-z0-9+\-.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def unique_in_order(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if pd.isna(value):
            continue
        text = str(value).strip()
        key = normalize_name(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            self.parent[left_root] = right_root
        elif self.rank[left_root] > self.rank[right_root]:
            self.parent[right_root] = left_root
        else:
            self.parent[right_root] = left_root
            self.rank[left_root] += 1


def representative_position(ra_values: pd.Series, dec_values: pd.Series) -> tuple[float, float]:
    """Return the spherical mean position in decimal degrees."""
    ra_rad = [math.radians(float(value)) for value in ra_values]
    dec_rad = [math.radians(float(value)) for value in dec_values]
    x = sum(math.cos(dec) * math.cos(ra) for ra, dec in zip(ra_rad, dec_rad))
    y = sum(math.cos(dec) * math.sin(ra) for ra, dec in zip(ra_rad, dec_rad))
    z = sum(math.sin(dec) for dec in dec_rad)
    radius = math.sqrt(x * x + y * y + z * z)
    if radius == 0:
        return float(ra_values.iloc[0]), float(dec_values.iloc[0])
    ra = math.degrees(math.atan2(y, x)) % 360.0
    dec = math.degrees(math.asin(z / radius))
    return ra, dec


def assign_components(resolved: pd.DataFrame) -> tuple[pd.Series, int]:
    sky = SkyCoord(
        ra=resolved["resolved_ra_deg"].to_numpy() * u.deg,
        dec=resolved["resolved_dec_deg"].to_numpy() * u.deg,
        frame="icrs",
    )
    left, right, _, _ = search_around_sky(
        sky,
        sky,
        MATCH_RADIUS_ARCSEC * u.arcsec,
    )

    uf = UnionFind(len(resolved))
    edge_count = 0
    for left_index, right_index in zip(left, right):
        if left_index < right_index:
            edge_count += 1
            uf.union(int(left_index), int(right_index))

    return pd.Series([uf.find(index) for index in range(len(resolved))]), edge_count


def build_entities(mentions: pd.DataFrame, coordinates: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, int]]:
    mentions = mentions.reset_index(names="mention_order")

    resolved = coordinates[coordinates["has_resolved_coordinates"].fillna(False)].copy()
    resolved = resolved.merge(
        mentions[["mention_id", "mention_order", "raw_name"]],
        on="mention_id",
        how="left",
        suffixes=("_coordinate", "_mention"),
    )
    resolved["raw_name"] = resolved["raw_name_mention"].fillna(
        resolved.get("raw_name_coordinate")
    )
    resolved = resolved.sort_values(["mention_order", "mention_id"]).reset_index(drop=True)

    components, edge_count = assign_components(resolved)
    resolved["component"] = components

    component_rows: list[dict[str, object]] = []
    grouped = resolved.groupby("component", sort=False)
    sort_keys: list[tuple[int, int]] = []
    for component, group in grouped:
        first_order = int(group["mention_order"].min())
        sort_keys.append((first_order, int(component)))

    component_order = {
        component: index + 1
        for index, (_, component) in enumerate(sorted(sort_keys))
    }

    for component, group in grouped:
        group = group.sort_values(["mention_order", "mention_id"])
        chosen_name = str(group.iloc[0]["raw_name"]).strip()
        ra_deg, dec_deg = representative_position(
            group["resolved_ra_deg"],
            group["resolved_dec_deg"],
        )
        component_rows.append(
            {
                "entity_id": f"gmw_{component_order[int(component)]:08d}",
                "chosen_name": chosen_name,
                "ra_deg": ra_deg,
                "dec_deg": dec_deg,
                "resolved_names": unique_in_order(group["resolved_name"]),
                "mention_ids": group["mention_id"].astype(str).tolist(),
            }
        )

    component_rows.sort(key=lambda row: row["entity_id"])
    counts = {
        "resolved_mentions": int(len(resolved)),
        "entities": int(len(component_rows)),
        "match_edges_within_1_arcsec": int(edge_count),
        "entities_with_multiple_resolved_names": int(
            sum(len(row["resolved_names"]) > 1 for row in component_rows)
        ),
    }
    return component_rows, counts


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize(groups: list[dict[str, object]], edge_count: int, mentions: list[dict], coordinates: list[dict]) -> dict:
    quotes = pq.read_table(ROOT / "data/quotes.parquet").to_pylist()
    papers = pq.read_table(ROOT / "data/papers.parquet").to_pylist()
    images = pq.read_table(ROOT / "data/image_manifest.parquet").to_pylist()
    quote_matches = read_csv(ROOT / "evaluation/quote_matches.csv")
    manual = read_csv(ROOT / "evaluation/manual_review.csv")

    located = [r for r in coordinates if r["has_resolved_coordinates"]]
    paper_counts = Counter(r["paper_id"] for r in mentions)
    sizes = [len(r["mention_ids"]) for r in groups]
    multiple = [n for n in sizes if n > 1]
    singletons = sum(n == 1 for n in sizes)
    tiers = Counter(r["match_tier"] for r in quote_matches)
    strict = tiers["raw_substring"] + tiers["normalized_whitespace_substring"]
    fragments = [r for r in quote_matches if r["match_tier"] == "unmatched"]
    fragmented_matches = sum(r["all_fragments_matched"] == "true" for r in fragments)
    identities = Counter(r["final_identity_assessment"] for r in manual)
    precision = [r for r in manual if r["precision_issue"] == "true"]

    return {
        "extraction": {
            "processed_papers": len(papers),
            "paper_statuses": dict(Counter(r["status"] for r in papers)),
            "historical_triage_labels": dict(Counter(r["gemini_decision"] for r in papers)),
            "mentions": len(mentions),
            "quotes": len(quotes),
            "papers_with_mentions": len(paper_counts),
            "mentions_with_extracted_paper_coordinates": sum(r["has_paper_coordinates"] for r in mentions),
            "papers_with_exactly_30_mentions": sum(n == 30 for n in paper_counts.values()),
            "papers_exceeding_30_mentions": {p: n for p, n in paper_counts.items() if n > 30},
        },
        "coordinates": {
            "initial_programmatic_attempted_mentions": sum(r["initial_ned_query_attempted"] for r in coordinates),
            "initial_programmatic_resolved_mentions": sum(r["initial_ned_resolution_status"] == "resolved" for r in coordinates),
            "final_resolved_mentions": len(located),
            "final_resolved_fraction": len(located) / len(coordinates),
            "final_without_coordinates": len(coordinates) - len(located),
            "final_valid_programmatic_mentions": sum(r["resolver_stage"] == "programmatic_ned" for r in located),
            "final_resolved_agent_statuses": dict(Counter(r["resolution_status"] for r in located if r["resolver_stage"] == "subagent")),
            "all_final_statuses": dict(Counter(r["resolution_status"] for r in coordinates)),
        },
        "grouping": {
            "radius_arcsec": MATCH_RADIUS_ARCSEC,
            "linked_pairs": edge_count,
            "entries": len(groups),
            "grouped_mentions": sum(sizes),
            "single_mention_entries": singletons,
            "single_mention_fraction": singletons / len(groups),
            "multiple_mention_entries": len(multiple),
            "median_mentions_in_multiple_mention_entries": median(multiple),
        },
        "images": {
            "images": len(images),
            "surveys": dict(Counter(r["hips"] for r in images)),
        },
        "saved_quote_evaluation": {
            "quotes": len(quote_matches),
            "continuous_match_tiers": dict(tiers),
            "raw_or_normalized_matches": strict,
            "raw_or_normalized_fraction": strict / len(quote_matches),
            "fragment_followup_quotes": len(fragments),
            "all_fragments_matched": fragmented_matches,
            "fragment_match_fraction": fragmented_matches / len(fragments),
            "fragment_followup_still_unmatched": len(fragments) - fragmented_matches,
        },
        "saved_manual_review": {
            "reviewed_records": len(manual),
            "initial_discussion_labels": dict(Counter(r["initial_discussion"] for r in manual)),
            "initial_coordinate_labels": dict(Counter(r["initial_coordinate"] for r in manual)),
            "final_identity_assessments": dict(identities),
            "supported_identity_fraction": identities["supported"] / len(manual),
            "precision_concerns": len(precision),
            "precision_concerns_in_supported_identities": sum(r["final_identity_assessment"] == "supported" for r in precision),
            "largest_documented_precision_issue_arcsec": max(float(r["separation_arcsec"]) for r in precision),
            "quotation_concerns": sum(r["quotation_concern"] == "true" for r in manual),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    mentions = pq.read_table(ROOT / "data/mentions.parquet").to_pylist()
    coordinates = pq.read_table(ROOT / "data/coordinates.parquet").to_pylist()
    groups, counts = build_entities(pd.DataFrame(mentions), pd.DataFrame(coordinates))

    # Published IDs are labels retained after invalidations removed empty entries.
    published = pq.read_table(ROOT / "data/galaxies.parquet")
    published_ids = {m: r["entity_id"] for r in published.to_pylist() for m in r["mention_ids"]}
    for group in groups:
        group["entity_id"] = published_ids[group["mention_ids"][0]]
    groups.sort(key=lambda r: r["entity_id"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(groups, schema=published.schema), args.output_dir / "galaxies.parquet")
    stats = summarize(groups, counts["match_edges_within_1_arcsec"], mentions, coordinates)
    result = json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
    (args.output_dir / "statistics.json").write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
