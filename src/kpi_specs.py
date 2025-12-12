# src/kpi_specs.py

KPI_SPECS = [
    {
        "name": "Total GHG emissions (Scope 1+2+3)",
        "category": "esg",
        "question": "What are EssilorLuxottica's total Scope 1, 2 and 3 emissions for FY24?",
        "unit": "tCO2e",
        "year": 2024,
        "allowed_doc_types": ["esg"],
    },
    {
        "name": "Scope 1 emissions",
        "category": "esg",
        "question": "What is the numeric value of EssilorLuxottica's Scope 1 emissions (in tCO2e) for FY24?",
        "unit": "tCO2e",
        "year": 2024,
        "allowed_doc_types": ["esg"],
    },
    {
        "name": "Scope 2 emissions (market-based)",
        "category": "esg",
        "question": "What is the numeric value of EssilorLuxottica's Scope 2 emissions (market-based, in tCO2e) for FY24?",
        "unit": "tCO2e",
        "year": 2024,
        "allowed_doc_types": ["esg"],
    },
    {
        "name": "Scope 3 emissions",
        "category": "esg",
        "question": "What are EssilorLuxottica's Scope 3 emissions for FY24?",
        "unit": "tCO2e",
        "year": 2024,
        "allowed_doc_types": ["esg"],
    },

    {
        "name": "Revenue",
        "category": "financial",
        "question": "What is EssilorLuxottica's total revenue for FY24?",
        "unit": "EUR bn",
        "year": 2024,
        "allowed_doc_types": ["financial", "annual"],
    },
    {
        "name": "EBITDA",
        "category": "financial",
        "question": "What is EssilorLuxottica's EBITDA for FY24?",
        "unit": "EUR bn",
        "year": 2024,
        "allowed_doc_types": ["financial", "annual"],
    },
    {
        "name": "Operating margin",
        "category": "financial",
        "question": "What is EssilorLuxottica's operating margin for FY24 (in %)?",
        "unit": "%",
        "year": 2024,
        "allowed_doc_types": ["financial", "annual"],
    },

    # --- EXTRA ESG KPI ---
    {
        "name": "Total GHG intensity",
        "category": "esg",
        "question": "What is EssilorLuxottica's total greenhouse gas emissions intensity (tCO2e per EUR million EVIC) for FY24?",
        "unit": "tCO2e / EURm EVIC",
        "year": 2024,
        "allowed_doc_types": ["esg"],
    },
]
