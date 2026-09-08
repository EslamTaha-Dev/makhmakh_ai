import json

import httpx

from app.core.config import get_settings


class OllamaError(Exception):
    pass


def generate_text(
    prompt: str,
    system: str | None = None,
) -> str:
    settings = get_settings()

    full_prompt = prompt

    if system:
        full_prompt = f"{system}\n\n{prompt}"

    payload = {
        "model": settings.ollama_model,
        "prompt": full_prompt,
        "stream": False,
    }

    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
            timeout=60.0,
            trust_env=False,
        )

        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise OllamaError(
            f"Ollama request failed: {exc}"
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise OllamaError(
            "Ollama returned invalid JSON"
        ) from exc

    answer = data.get("response")

    if not answer:
        raise OllamaError(
            "Ollama returned an empty response"
        )

    return answer


def _extract_json(text: str):
    cleaned = text.strip()

    # Remove Markdown code fences
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    # First try the complete response
    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass

    # Try to extract a JSON object
    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")

    if object_start != -1 and object_end > object_start:
        candidate = cleaned[object_start:object_end + 1]

        try:
            return json.loads(candidate)

        except json.JSONDecodeError:
            pass

    # Try to extract a JSON array
    array_start = cleaned.find("[")
    array_end = cleaned.rfind("]")

    if array_start != -1 and array_end > array_start:
        candidate = cleaned[array_start:array_end + 1]

        try:
            return json.loads(candidate)

        except json.JSONDecodeError:
            pass

    raise OllamaError(
        f"Ollama did not return valid JSON. Response was: {cleaned[:1000]}"
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
            "Ollama returned valid JSON, but the result is not a JSON object"
        )

    return result
