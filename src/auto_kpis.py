# src/auto_kpis.py

from __future__ import annotations
from typing import Any, Dict, List
import pathlib

import pandas as pd

from .kpi_specs import KPI_SPECS
from .llm_agent import extract_kpi_numeric


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = DATA_DIR / "kpis_auto.csv"


def build_auto_kpis() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for spec in KPI_SPECS:
        q = spec["question"]
        allowed_doc_types = spec.get("allowed_doc_types")
        unit = spec["unit"]

        print(f"\n=== Querying KPI: {spec['name']} ===")
        print(f"Question: {q}")
        print(f"Allowed doc_types: {allowed_doc_types}")

        result = extract_kpi_numeric(
            question=q,
            expected_unit=unit,
            allowed_doc_types=allowed_doc_types,
            k=8,
        )

        value = result.get("value")
        unit_returned = result.get("unit") or unit
        chunk_ids = result.get("chunk_ids", [])
        confidence = result.get("confidence", "unknown")
        reason = result.get("reason", "")
        raw_snippet = result.get("raw_snippet", "")
        chunks_df = result["chunks"]

        row = {
            "name": spec["name"],
            "category": spec["category"],
            "value": value,
            "unit": unit_returned,
            "year": spec["year"],
            "description": q,
            "source": ", ".join(chunks_df["source"].unique()),
            "chunk_ids": ", ".join(map(str, chunk_ids)),
            "confidence": confidence,
            "reason": reason,
            "raw_snippet": raw_snippet,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def sanity_checks(df: pd.DataFrame) -> None:
    """
    Example sanity check: total GHG vs sum of Scopes 1, 2, 3.
    """
    try:
        total = df.loc[df["name"] == "Total GHG emissions (Scope 1+2+3)", "value"].iloc[0]
        s1 = df.loc[df["name"] == "Scope 1 emissions", "value"].iloc[0]
        s2 = df.loc[df["name"] == "Scope 2 emissions (market-based)", "value"].iloc[0]
        s3 = df.loc[df["name"] == "Scope 3 emissions", "value"].iloc[0]

        approx_sum = s1 + s2 + s3
        diff = abs(total - approx_sum)

        print("\n=== Sanity check: Total vs Scope 1+2+3 ===")
        print(f"Total: {total}")
        print(f"Sum(Scopes): {approx_sum}")
        print(f"Difference: {diff}")
    except Exception as e:
        print("Check failed:", e)


def main():
    df = build_auto_kpis()
    sanity_checks(df)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved auto KPIs to {OUTPUT_CSV}\n")
    print(df)


if __name__ == "__main__":
    main()
