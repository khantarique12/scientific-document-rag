
"""Benchmark examples for evaluating citation grounding."""

CITATION_BENCHMARK = [
    {
        "id": "smart_supported",
        "claim": (
            "The SMART criteria are Specific, Measurable, "
            "Achievable, Relevant, and Time-bound."
        ),
        "evidence": (
            "The SMART framework ensures that effective KPIs "
            "adhere to the SMART criteria: "
            "Specific: Clear and well-defined objectives. "
            "Measurable: Quantifiable data points. "
            "Achievable: Realistic targets. "
            "Relevant: Alignment with organizational goals. "
            "Time-bound: Defined time frames."
        ),
        "supported": True,
    },
    {
        "id": "smart_unrelated",
        "claim": (
            "The SMART criteria are Specific, Measurable, "
            "Achievable, Relevant, and Time-bound."
        ),
        "evidence": (
            "KPIs represent measurable outcomes describing "
            "an organization's ability to reach its "
            "business objectives. KPIs can be financial, "
            "operational, or strategic."
        ),
        "supported": False,
    },
    {
        "id": "smart_partial",
        "claim": (
            "The SMART criteria are Specific, Measurable, "
            "Achievable, Relevant, and Time-bound."
        ),
        "evidence": (
            "The SMART criteria include Specific and "
            "Measurable objectives."
        ),
        "supported": False,
    },
    {
        "id": "rdf_supported",
        "claim": (
            "RDF represents information using "
            "subject-predicate-object triples."
        ),
        "evidence": (
            "An RDF statement consists of a subject, "
            "a predicate, and an object."
        ),
        "supported": True,
    },
    {
        "id": "rdf_unsupported",
        "claim": (
            "RDF represents information using "
            "subject-predicate-object triples."
        ),
        "evidence": (
            "SPARQL is a query language used to "
            "retrieve information from RDF datasets."
        ),
        "supported": False,
    },
    {
        "id": "contradiction",
        "claim": (
            "The framework uses five SMART criteria."
        ),
        "evidence": (
            "The proposed framework uses only "
            "three evaluation criteria."
        ),
        "supported": False,
    },
]
