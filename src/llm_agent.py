
import os
import textwrap
import json
import pandas as pd

from openai import OpenAI
from .retrieval import retrieve_chunks


# ----------------------------------------------------
#LLM CLIENT
# ----------------------------------------------------
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(prompt: str) -> str:
    """
    Real LLM API call using OpenAI models.
    Uses gpt-4.1-mini for low latency + low hallucination risk.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Environment variable OPENAI_API_KEY is not set.\n"
            "Set it before running the notebook."
        )

    try:
        response = _client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        # New OpenAI
        return response.choices[0].message.content

    except Exception as e:
        # Fallback
        return f"LLM CALL FAILED: {type(e).__name__}: {e}\n\n--- PROMPT PREVIEW ---\n\n{prompt}"


# ----------------------------------------------------
# CONTEXT BUILDING
# ----------------------------------------------------
def build_context_string(chunks_df: pd.DataFrame) -> str:
    """
    Convert retrieved chunk rows into a formatted string
    that will be inserted into the prompt.
    """
    blocks = []

    for _, row in chunks_df.iterrows():
        header = (
            f"[chunk_id={row['chunk_id']}, "
            f"source={row['source']}, "
            f"doc_type={row['doc_type']}, "
            f"year={row['year']}]"
        )

        text = str(row["text"])
        blocks.append(header + "\n" + text)

    return "\n\n".join(blocks)


# ----------------------------------------------------
# GENERIC RAG PROMPT FOR ANSWER QUESTION
# ----------------------------------------------------
def build_prompt(question: str, chunks_df: pd.DataFrame) -> str:
    """
    Produce the final strict RAG prompt for general Q&A.
    """
    context = build_context_string(chunks_df)

    template = f"""
    You are a financial and ESG analyst answering questions about EssilorLuxottica.

    Use ONLY the information provided in the text chunks below.
    If the answer does not appear in the chunks, respond exactly:
    "Based on the provided documents, this information is not available."

    Rules:
    1. Cite chunk_ids like this: [chunk_id=5].
    2. Do NOT introduce information that is not in the chunks.
    3. Keep the answer to 3–5 sentences.
    4. If chunks conflict, choose the one with the most recent year.

    User question:
    {question}

    Retrieved chunks:
    {context}

    Now provide:
    1. A direct answer (3–5 sentences).
    2. A short note on missing or uncertain information.
    3. A list of chunk_ids used.
    """

    return textwrap.dedent(template).strip()


def answer_question(
    question: str,
    k: int = 6,
    allowed_doc_types: list[str] | None = None,
) -> dict:
    """
    General RAG Q&A:
    1. Retrieve relevant chunks
    2. Build a prompt
    3. Call the LLM
    4. Return answer + chunks + prompt
    """
    chunks = retrieve_chunks(
        question,
        k=k,
        allowed_doc_types=allowed_doc_types,
    )

    prompt = build_prompt(question, chunks)
    answer = call_llm(prompt)

    return {
        "answer": answer,
        "chunks": chunks,
        "prompt_used": prompt,
    }


# ----------------------------------------------------
# KPI-SPECIFIC NUMERIC EXTRACTOR (JSON OUTPUT)
# ----------------------------------------------------
def extract_kpi_numeric(
    question: str,
    expected_unit: str,
    k: int = 8,
    allowed_doc_types: list[str] | None = None,
) -> dict:
    """
    Specialized pipeline for extracting a SINGLE numeric KPI.

    Returns a dict with:
      - value (float or None)
      - unit (string or None)
      - chunk_ids (list[int])
      - confidence ("high"/"medium"/"low")
      - reason (short explanation)
      - raw_snippet (where the number came from)
      - raw_response (raw JSON or LLM text)
      - chunks (DataFrame of retrieved chunks)
    """
    # Retrieve relevant chunks
    chunks = retrieve_chunks(
        question,
        k=k,
        allowed_doc_types=allowed_doc_types,
    )

    context = build_context_string(chunks)

    # JSON prompt
    template = f"""
    You are extracting a single numeric KPI for EssilorLuxottica.

    User KPI question:
    {question}

    Expected unit for the answer: "{expected_unit}"

    You are given text chunks from official reports. Use ONLY these chunks.
    If the exact value is not present, say so.

    Text chunks:
    {context}

    TASK:
    - Find the SINGLE most relevant numeric value that answers the question.
    - Copy the number EXACTLY as written (do NOT round, do NOT change commas).
    - Use only the expected unit if it matches (otherwise explain the mismatch).
    - Identify which chunk_ids support the value.

    Respond ONLY with a valid JSON object in this exact format:

    {{
      "value": <number or null>,
      "unit": "<unit string or null>",
      "chunk_ids": [<list of integers>],
      "confidence": "<high|medium|low>",
      "reason": "<short explanation>",
      "raw_snippet": "<short snippet where you found the number>"
    }}

    If the value is not in the text, set "value" to null and explain in "reason".
    """

    prompt = textwrap.dedent(template).strip()
    raw = call_llm(prompt)

    #Try to parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if model output isn't valid JSON
        return {
            "value": None,
            "unit": None,
            "chunk_ids": [],
            "confidence": "low",
            "reason": f"Failed to parse JSON. Raw response not valid JSON.",
            "raw_snippet": "",
            "raw_response": raw,
            "chunks": chunks,
        }

    # Attach supporting info
    data["raw_response"] = raw
    data["chunks"] = chunks

    # Normalize some fields
    if "chunk_ids" not in data or not isinstance(data["chunk_ids"], list):
        data["chunk_ids"] = []

    return data
