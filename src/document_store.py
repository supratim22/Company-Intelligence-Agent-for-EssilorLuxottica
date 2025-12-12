
from pathlib import Path
import pandas as pd

# Project path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_raw_chunks() -> pd.DataFrame:
    """Load the raw Essilor chunk CSV exactly as saved."""
    path = DATA_DIR / "essilor_chunks_clean.csv"
    df = pd.read_csv(path)
    return df


def _infer_doc_type(source_file: str) -> str:
    """Map file names to a coarse document type."""
    s = str(source_file).lower()

    if "esg" in s or "sustain" in s:
        return "esg"
    if "factset" in s and ("fin" in s or "financial" in s):
        return "financial"
    if "annual" in s or "10k" in s or "report" in s:
        return "annual"
    if "external" in s or "press" in s or "stellest" in s or "summary" in s:
        return "news"
    return "other"


def _infer_year(source_file: str) -> int:
    """Very simple year inference from file name."""
    s = str(source_file)
    for y in ("2023", "2024", "2025"):
        if y in s:
            return int(y)
    # Default for this project
    return 2024


def build_document_store() -> pd.DataFrame:
    """
    Normalise the raw chunk dataframe to a standard schema.

    Output columns:
      - chunk_id : unique ID per chunk
      - text     : chunk content
      - source   : original file name
      - doc_type : coarse type (esg, financial, annual, news, other)
      - year     : year we attribute to the document
    """
    df = load_raw_chunks()

    # Rename to our standard names
    rename_map = {
        "chunk_text": "text",
        "source_file": "source",
    }
    df = df.rename(columns=rename_map)

    # Make sure required columns exist
    required = ["chunk_id", "text", "source"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column in raw CSV: {col}")


    df["doc_type"] = df["source"].apply(_infer_doc_type)
    df["year"] = df["source"].apply(_infer_year)

    # Keep only what we need, in a fixed order
    df = df[["chunk_id", "text", "source", "doc_type", "year"]].copy()

    return df


def save_document_store_parquet() -> None:
    """
    Optional: save the normalised document store to Parquet
    for faster loading in the app.
    """
    df = build_document_store()
    models_dir = PROJECT_ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_path = models_dir / "document_store.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Saved document_store.parquet with {len(df)} rows to {out_path}")
