import json

from app.ai.ai_gateway.ai_gateway import AIGatewayError, ai_gateway_execute


class OllamaError(Exception):
    pass


def generate_text(
    prompt: str,
    system: str | None = None,
) -> str:
    full_prompt = prompt

    if system:
        full_prompt = f"{system}\n\n{prompt}"

    try:
        return ai_gateway_execute(
            task_type="document_understanding",
            prompt=full_prompt,
        )
    except AIGatewayError as exc:
        raise OllamaError(f"AI text generation failed: {exc}") from exc


def _extract_json(text: str):
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")

    if object_start != -1 and object_end > object_start:
        candidate = cleaned[object_start:object_end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    array_start = cleaned.find("[")
    array_end = cleaned.rfind("]")

    if array_start != -1 and array_end > array_start:
        candidate = cleaned[array_start:array_end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise OllamaError(
        f"AI provider did not return valid JSON. Response was: {cleaned[:1000]}"
    )


def generate_json(
    prompt: str,
    system: str | None = None,
) -> dict:
    response = generate_text(
        prompt=prompt,
        system=system,
    )

    result = _extract_json(response)

    if not isinstance(result, dict):
        raise OllamaError(
            "AI provider returned valid JSON, but the result is not a JSON object"
        )

    return result
