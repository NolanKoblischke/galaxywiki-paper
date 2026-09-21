"""Historical candidate-query rules for the programmatic NED pass.

This module generates queries; it does not call NED. The original Abell
pattern is preserved, including bare A identifiers; 112 false matches were
subsequently excluded from the released coordinates.
"""

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
