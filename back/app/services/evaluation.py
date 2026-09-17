from app.services.rag_chat import answer_question


def evaluate_question(course_id: str, question: str) -> dict:
    question = question.strip()

    if not question:
        return {
            "question": question,
            "answer": "",
            "source_count": 0,
            "has_sources": False,
            "passed": False,
            "error": "Question cannot be empty",
        }

    try:
        result = answer_question(
            course_id=course_id,
            question=question,
        )

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        if not isinstance(answer, str):
            answer = ""

        if not isinstance(sources, list):
            sources = []

        answer = answer.strip()

        return {
            "question": question,
            "answer": answer,
            "source_count": len(sources),
            "has_sources": bool(sources),
            "passed": bool(answer) and bool(sources),
        }

    except Exception as exc:
        return {
            "question": question,
            "answer": "",
            "source_count": 0,
            "has_sources": False,
            "passed": False,
            "error": str(exc),
        }


def evaluate_questions(course_id: str, questions: list[str]) -> dict:
    results = []

    for question in questions:
        results.append(
            evaluate_question(
                course_id=course_id,
                question=question,
            )
        )

    total = len(results)
    passed = sum(
        1 for result in results
        if result["passed"]
    )
    failed = total - passed

    score = passed / total if total else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": score,
        "results": results,
    }