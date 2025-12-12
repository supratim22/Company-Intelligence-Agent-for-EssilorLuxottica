# src/kpis.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Dict, Any

import pandas as pd
import pathlib


def _parse_value(raw) -> float | None:
    """
    Safely convert raw CSV 'value' into a float.

    Handles:
    - numeric types
    - strings like '17%' or '1,234.56'
    - empty / invalid values -> None
    """
    import math

    if pd.isna(raw):
        return None

    # Already numeric
    if isinstance(raw, (int, float)):
        if isinstance(raw, float) and math.isnan(raw):
            return None
        return float(raw)

    # String case
    s = str(raw).strip()
    if not s:
        return None

    # Remove thousands separators
    s = s.replace(",", "")

    # Drop trailing %
    if s.endswith("%"):
        s = s[:-1].strip()

    try:
        return float(s)
    except ValueError:
        # If it's still not parsable, return None
        return None


Category = Literal["financial", "esg", "other"]


@dataclass
class KPI:
    name: str
    category: Category
    value: float | None
    unit: str
    year: int
    description: str
    source: str
    chunk_ids: list[int]
    confidence: str
    reason: str
    raw_snippet: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "value": self.value,
            "unit": self.unit,
            "year": self.year,
            "description": self.description,
            "source": self.source,
            "chunk_ids": ", ".join(map(str, self.chunk_ids)),
            "confidence": self.confidence,
            "reason": self.reason,
            "raw_snippet": self.raw_snippet,
            "notes": self.notes,
        }


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
AUTO_KPI_CSV = DATA_DIR / "kpis_auto.csv"


def _build_kpis() -> List[KPI]:
    if not AUTO_KPI_CSV.exists():
        raise FileNotFoundError(
            f"{AUTO_KPI_CSV} not found. Run auto_kpis.py to generate it first."
        )

    df = pd.read_csv(AUTO_KPI_CSV)

    kpis: List[KPI] = []
    for _, row in df.iterrows():
        chunk_ids: list[int] = []
        if isinstance(row.get("chunk_ids"), str) and row["chunk_ids"].strip():
            chunk_ids = [
                int(x) for x in row["chunk_ids"].split(",") if x.strip().isdigit()
            ]

        kpi = KPI(
            name=row["name"],
            category=row["category"],
            value=_parse_value(row["value"]),   # safe parser
            unit=row["unit"],
            year=int(row["year"]),
            description=row.get("description", ""),
            source=row.get("source", ""),
            chunk_ids=chunk_ids,
            confidence=row.get("confidence", ""),
            reason=row.get("reason", ""),
            raw_snippet=row.get("raw_snippet", ""),
            notes="",
        )
        kpis.append(kpi)

    return kpis


_ALL_KPIS: List[KPI] = _build_kpis()


def get_kpis(category: Category | None = None) -> list[KPI]:
    if category is None:
        return list(_ALL_KPIS)
    return [k for k in _ALL_KPIS if k.category == category]


def get_kpis_df(category: Category | None = None) -> pd.DataFrame:
    kpis = get_kpis(category)
    return pd.DataFrame([k.to_dict() for k in kpis])
