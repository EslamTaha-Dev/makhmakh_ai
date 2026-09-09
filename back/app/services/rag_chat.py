from app.ai.ollama_client import generate_text
from app.ai.rag_prompt import (
    SYSTEM_PROMPT,
    build_rag_prompt,
)
from app.services.retrieval import search_similar_chunks


def answer_question(
    course_id: str,
    question: str,
    top_k: int = 5,
) -> dict:
    question = question.strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "sources": [],
        }

    results = search_similar_chunks(
        course_id=course_id,
        query=question,
        top_k=top_k,
    )

    if not results:
        return {
            "answer": (
                "I don't have enough information in the provided "
                "course material to answer this question."
            ),
            "sources": [],
        }

    context_parts = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"""
SOURCE {index}
FILE: {result["file_name"]}
DISTANCE: {result["distance"]}

CONTENT:
{result["text"]}
""".strip()
        )

    context = "\n\n".join(context_parts)

    prompt = build_rag_prompt(
        question=question,
        context=context,
    )

    answer = generate_text(
        prompt=prompt,
        system=SYSTEM_PROMPT,
    )

    sources = [
        {
            "chunk_id": result["chunk_id"],
            "material_id": result["material_id"],
            "text": result["text"],
            "file_name": result["file_name"],
            "distance": result["distance"],
        }
        for result in results
    ]

    return {
        "answer": answer.strip(),
        "sources": sources,
    }