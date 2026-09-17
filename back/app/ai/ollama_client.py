import json
import os
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

    api_keys = [
        os.getenv("GEMINI_API_KEY_PRIMARY"),
        os.getenv("GEMINI_API_KEY_BACKUP"),
        os.getenv("OPENROUTER_API_KEY")
    ]
    api_keys = [key for key in api_keys if key]

    if not api_keys:
        api_keys = [None]

    last_error = None

    for index, api_key in enumerate(api_keys):
        try:
            headers = {}
            
            if api_key and api_key.startswith("sk-or"):
                headers["Authorization"] = f"Bearer {api_key}"
                headers["HTTP-Referer"] = "https://github.com/EslamTaha-Dev/makhmakh_ai"
                headers["X-Title"] = "Makhmakh AI"
                
                request_url = "https://openrouter.ai/api/v1/chat/completions"
                
                openrouter_payload = {
                    "model": "google/gemini-2.5-flash",
                    "messages": [{"role": "user", "content": full_prompt}]
                }
                
                response = httpx.post(
                    request_url,
                    json=openrouter_payload,
                    headers=headers,
                    timeout=60.0,
                    trust_env=False,
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("choices", [{}])[0].get("message", {}).get("content")

            else:
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                response = httpx.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                    trust_env=False,
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("response")

            if answer:
                return answer

        except (httpx.HTTPError, Exception) as exc:
            last_error = exc
            continue

    raise OllamaError(
        f"فشلت كل المفاتيح والمصادر المتاحة. الخطأ الأخير: {last_error}"
    )


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