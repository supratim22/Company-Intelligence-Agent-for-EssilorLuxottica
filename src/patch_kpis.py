
from __future__ import annotations
from pathlib import Path

import pandas as pd


def main():
    project_root = Path(__file__).resolve().parents[1]
    csv_path = project_root / "data" / "kpis_auto.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found. Run auto_kpis.py first.")

    df = pd.read_csv(csv_path)

    # Manual, verified values from ESG report:
    scope1_value = 116_092
    scope2_value = 475_555

    # Patch Scope 1
    mask_s1 = df["name"] == "Scope 1 emissions"
    df.loc[mask_s1, "value"] = scope1_value
    df.loc[mask_s1, "confidence"] = "manual"
    df.loc[mask_s1, "reason"] = "Manually set from verified ESG figures."

    # Patch Scope 2
    mask_s2 = df["name"] == "Scope 2 emissions (market-based)"
    df.loc[mask_s2, "value"] = scope2_value
    df.loc[mask_s2, "confidence"] = "manual"
    df.loc[mask_s2, "reason"] = "Manually set from verified ESG figures."

    df.to_csv(csv_path, index=False)

    print("Patched Scope 1 and Scope 2 values in kpis_auto.csv:")
    print(df[["name", "value", "unit", "confidence"]])


if __name__ == "__main__":
    main()
