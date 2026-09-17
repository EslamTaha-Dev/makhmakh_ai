from sqlalchemy import select

from app.ai.ai_gateway.ai_gateway import ai_gateway_execute
from app.ai.rag_prompt import (
    SYSTEM_PROMPT,
    build_rag_prompt,
)
from app.db.session import SessionLocal
from app.models.concept import Concept, ConceptPrerequisite
from app.services.retrieval import search_similar_chunks


def _get_graph_context(
    course_id: str,
    results: list[dict],
) -> str:
    db = SessionLocal()

    try:
        relevant_concept_ids = set()

        for result in results:
            for concept in result.get(
                "related_concepts",
                [],
            ):
                relevant_concept_ids.add(
                    concept["id"]
                )

        if not relevant_concept_ids:
            return ""

        concepts = db.scalars(
            select(Concept).where(
                Concept.id.in_(
                    list(relevant_concept_ids)
                )
            )
        ).all()

        concept_by_id = {
            str(concept.id): concept
            for concept in concepts
        }

        prerequisite_ids = set()

        relations = db.scalars(
            select(ConceptPrerequisite).where(
                ConceptPrerequisite.concept_id.in_(
                    list(relevant_concept_ids)
                )
            )
        ).all()

        for relation in relations:
            prerequisite_ids.add(
                str(relation.prerequisite_concept_id)
            )

        prerequisites = []

        if prerequisite_ids:
            prerequisites = db.scalars(
                select(Concept).where(
                    Concept.id.in_(
                        list(prerequisite_ids)
                    )
                )
            ).all()

        parts = []

        for concept in concepts:
            parts.append(
                f"""
CONCEPT:
{concept.name}

DESCRIPTION:
{concept.description or "No description available."}
""".strip()
            )

        for prerequisite in prerequisites:
            parent_concepts = [
                concept_by_id.get(
                    str(relation.concept_id)
                )
                for relation in relations
                if str(
                    relation.prerequisite_concept_id
                ) == str(prerequisite.id)
            ]

            parent_names = [
                concept.name
                for concept in parent_concepts
                if concept is not None
            ]

            parts.append(
                f"""
PREREQUISITE CONCEPT:
{prerequisite.name}

DESCRIPTION:
{prerequisite.description or "No description available."}

USED BY:
{", ".join(parent_names)}
""".strip()
            )

        return "\n\n".join(parts)

    finally:
        db.close()


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

    for index, result in enumerate(
        results,
        start=1,
    ):
        context_parts.append(
            f"""
SOURCE {index}
FILE: {result["file_name"]}
DISTANCE: {result["distance"]}
GRAPH_RELEVANT: {result.get("graph_relevant", False)}

CONTENT:
{result["text"]}
""".strip()
        )

    vector_context = "\n\n".join(context_parts)

    graph_context = _get_graph_context(
        course_id=course_id,
        results=results,
    )

    if graph_context:
        context = (
            "VECTOR RETRIEVAL CONTEXT\n"
            "========================\n"
            f"{vector_context}\n\n"
            "KNOWLEDGE GRAPH CONTEXT\n"
            "=======================\n"
            f"{graph_context}"
        )
    else:
        context = vector_context

    prompt = build_rag_prompt(
        question=question,
        context=context,
    )

    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

    answer = ai_gateway_execute(
        task_type="document_understanding",
        prompt=full_prompt,
    )

    sources = [
        {
            "chunk_id": result["chunk_id"],
            "material_id": result["material_id"],
            "text": result["text"],
            "file_name": result["file_name"],
            "distance": result["distance"],
            "related_concepts": result.get(
                "related_concepts",
                [],
            ),
        }
        for result in results
    ]

    return {
        "answer": answer.strip(),
        "sources": sources,
    }