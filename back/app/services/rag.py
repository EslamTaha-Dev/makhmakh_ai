from app.services.retrieval import search_similar_chunks


def build_context(results: list[dict]) -> str:
    if not results:
        return ""

    parts = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        graph_info = result.get(
            "related_concepts",
            [],
        )

        concept_text = ""

        if graph_info:
            concept_lines = []

            for concept in graph_info:
                concept_lines.append(
                    f"- {concept['name']}: "
                    f"{concept.get('description', '')}"
                )

            concept_text = (
                "\nRELATED CONCEPTS:\n"
                + "\n".join(concept_lines)
            )

        parts.append(
            f"""
SOURCE {index}
FILE: {result["file_name"]}
CHUNK_ID: {result["chunk_id"]}
DISTANCE: {result["distance"]}

{result["text"]}
{concept_text}
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