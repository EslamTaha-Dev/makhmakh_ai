from collections import OrderedDict

from app.ai.concept_extractor import extract_concepts


BATCH_SIZE = 2


def _safe_string(value) -> str:
    if value is None:
        return ""

    if not isinstance(value, str):
        return str(value)

    return value.strip()


def extract_course_concepts(
    chunks: list[str],
) -> dict:
    concepts = OrderedDict()
    prerequisites = []

    valid_chunks = []

    for chunk in chunks:
        if not isinstance(chunk, str):
            continue

        chunk = chunk.strip()

        if not chunk:
            continue

        valid_chunks.append(chunk)

    # Process several chunks in one Ollama request.
    for start in range(
        0,
        len(valid_chunks),
        BATCH_SIZE,
    ):
        batch = valid_chunks[
            start:start + BATCH_SIZE
        ]

        combined_text = "\n\n".join(
            f"CHUNK {index + 1}:\n{text}"
            for index, text in enumerate(batch)
        )

        try:
            result = extract_concepts(
                combined_text
            )

        except Exception as exc:
            print(
                f"Concept extraction failed for batch "
                f"{start // BATCH_SIZE + 1}: {exc}"
            )
            continue

        if not isinstance(result, dict):
            continue

        raw_concepts = result.get(
            "concepts",
            [],
        )

        if not isinstance(
            raw_concepts,
            list,
        ):
            raw_concepts = []

        for concept in raw_concepts:
            if not isinstance(
                concept,
                dict,
            ):
                continue

            name = _safe_string(
                concept.get("name")
            )

            if not name:
                continue

            key = name.lower()

            if key not in concepts:
                concepts[key] = {
                    "name": name,
                    "description": _safe_string(
                        concept.get(
                            "description"
                        )
                    ),
                    "order_index": len(
                        concepts
                    ),
                }

        raw_prerequisites = result.get(
            "prerequisites",
            [],
        )

        if not isinstance(
            raw_prerequisites,
            list,
        ):
            raw_prerequisites = []

        for relation in raw_prerequisites:
            if not isinstance(
                relation,
                dict,
          ):
                continue

            concept = _safe_string(
                relation.get("concept")
            )

            prerequisite = _safe_string(
                relation.get("prerequisite")
            )

            if concept and prerequisite:
                prerequisites.append(
                    {
                        "concept": concept,
                        "prerequisite": prerequisite,
                    }
                )

        print(
            f"Concept batch "
            f"{start // BATCH_SIZE + 1} "
            f"processed."
        )

    return {
        "concepts": list(
            concepts.values()
        ),
        "prerequisites": prerequisites,
    }
