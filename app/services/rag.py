from app.services.retrieval import search_similar_chunks


def build_context(results: list[dict]) -> str:
    if not results:
        return ""

    parts = []

    for index, result in enumerate(results, start=1):
        parts.append(
            f"""
SOURCE {index}
FILE: {result["file_name"]}
CHUNK_ID: {result["chunk_id"]}

{result["text"]}
""".strip()
        )

    return "\n\n".join(parts)


def retrieve_context(
    course_id,
    question: str,
    top_k: int = 5,
):
    results = search_similar_chunks(
        course_id=course_id,
        query=question,
        top_k=top_k,
    )

    context = build_context(results)

    return context, results