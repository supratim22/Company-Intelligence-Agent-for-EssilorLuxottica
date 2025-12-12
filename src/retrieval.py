from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .document_store import build_document_store, PROJECT_ROOT



MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
MATRIX_PATH = MODELS_DIR / "tfidf_matrix.joblib"
DOCSTORE_PATH = MODELS_DIR / "document_store.parquet"




def build_tfidf_artifacts() -> None:
    """
    Build and save:
    - normalized document store (Parquet)
    - fitted TF-IDF vectorizer
    - TF-IDF matrix for all chunks
    """
    # Get clean document store
    df = build_document_store()

    # Fit TF-IDF on chunk texts
    texts = df["text"].astype(str).tolist()

    vectorizer = TfidfVectorizer(
        max_df=0.9,
        min_df=1,
        ngram_range=(1, 2),
        stop_words="english"
    )
    X = vectorizer.fit_transform(texts)

    # Save everything
    df.to_parquet(DOCSTORE_PATH, index=False)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(X, MATRIX_PATH)

    print(f"Saved TF-IDF artifacts: {len(df)} chunks, matrix shape {X.shape}")




def load_tfidf_artifacts():
    """
    Load document store, TF-IDF vectorizer, and TF-IDF matrix.
    """
    df = pd.read_parquet(DOCSTORE_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    X = joblib.load(MATRIX_PATH)
    return df, vectorizer, X




def retrieve_chunks(
    question: str,
    k: int = 5,
    allowed_doc_types: list[str] | None = None,
) -> pd.DataFrame:
    """
    Retrieve top-k chunks most relevant to the question.

    Parameters
    ----------
    question : str
        User's question in plain language.
    k : int
        Number of chunks to return.
    allowed_doc_types : list[str] | None
        If provided, restrict search to these doc_types,
        e.g. ["esg"], ["financial", "annual"].

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: chunk_id, text, source, doc_type, year, similarity
        sorted by similarity descending.
    """
    df, vectorizer, X = load_tfidf_artifacts()

    # Optional filter on doc_type
    if allowed_doc_types is not None:
        mask = df["doc_type"].isin(allowed_doc_types)
        df_sub = df[mask].reset_index(drop=True)
        X_sub = X[mask.values]
    else:
        df_sub = df
        X_sub = X

    if df_sub.empty:
        raise ValueError("No documents available for the given allowed_doc_types.")

    # Vectorize question
    q_vec = vectorizer.transform([str(question)])

    # Cosine similarity between question and all candidate chunks
    sims = cosine_similarity(q_vec, X_sub).flatten()

    # Get indices of top-k similarities
    k = min(k, len(sims))
    top_idx = np.argsort(sims)[::-1][:k]

    results = df_sub.iloc[top_idx].copy()
    results["similarity"] = sims[top_idx]

    # Sort by similarity descending just to be explicit
    results = results.sort_values("similarity", ascending=False).reset_index(drop=True)
    return results
