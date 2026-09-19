import json
import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agent import plan_tool
from app.ai.ai_gateway.ai_gateway import (
    ai_gateway_execute,
    get_configured_llm_model,
)
from app.services.tools.agent_tools import (
    search_course_content,
    get_student_progress,
    get_graph_context,
    recommend_next_step,
)


def _json_default(value):
    if isinstance(value, UUID):
        return str(value)

    raise TypeError(
        f"Object of type {type(value).__name__} " "is not JSON serializable"
    )


def run_agent(
    db: Session,
    user_id,
    course_id: str,
    question: str,
    node_id: str | None = None,
) -> dict:

    started_at = time.perf_counter()

    plan = plan_tool(question)

    tool_name = plan["tool"]
    arguments = plan.get("arguments", {})

    if tool_name == "search_course_content":
        tool_result = search_course_content(
            db=db,
            course_id=course_id,
            query=arguments.get("query", question),
            node_id=arguments.get("node_id") or node_id,
            top_k=arguments.get("top_k", 5),
        )

    elif tool_name == "get_student_progress":
        tool_result = get_student_progress(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )

    elif tool_name == "get_graph_context":
        tool_result = get_graph_context(
            db=db,
            course_id=course_id,
            concept_name=arguments.get("concept_name"),
        )

    elif tool_name == "recommend_next_step":
        tool_result = recommend_next_step(
            db=db,
            user_id=user_id,
            course_id=course_id,
        )

    else:
        raise ValueError(f"Unsupported agent tool: {tool_name}")

    tool_payload = json.dumps(
        tool_result,
        ensure_ascii=False,
        default=_json_default,
    )

    final_prompt = f"""
You are makhmakh, an educational assistant.

Answer the student's question using ONLY the information
returned by the backend tool.

Do not invent information.

LANGUAGE AND TONE RULES:
- Follow an explicit language request from the student, such as
    "answer in English", "answer in Arabic", or "بالعامية".
- Otherwise, answer in the primary language used in the student's question.
- If the student asks for colloquial Arabic or uses colloquial Arabic,
    answer in natural colloquial Arabic and do not rewrite it in formal Arabic.
- If the question is in English, answer in English. If it is in Arabic,
    answer in Arabic. Do not switch languages unless the student asks you to.
- Keep the requested language and tone consistent throughout the answer.
- Technical terms may remain in their commonly used form when translating
    them would make the explanation less clear.

If the tool result does not contain enough information,
say that the available course/student data is insufficient.

STUDENT QUESTION:
{question}

TOOL USED:
{tool_name}

TOOL RESULT:
{tool_payload}

Return only the final answer for the student.
"""

    answer = ai_gateway_execute(task_type="chat", prompt=final_prompt)

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    return {
        "answer": answer.strip(),
        "tool_name": tool_name,
        "tool_result": tool_result,
        "latency_ms": latency_ms,
        "model": get_configured_llm_model(),
        "fallback_mode": "rag",
    }
