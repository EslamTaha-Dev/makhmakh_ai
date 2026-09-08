import json
import re

from app.ai.ollama_client import generate_text


def generate_lesson_script(
    concept_name: str,
    concept_description: str,
) -> dict:
    prompt = f"""
You are an expert educational content creator.

Create a short educational lesson for a university student.

CONCEPT:
{concept_name}

DESCRIPTION:
{concept_description}

Return ONLY valid JSON using exactly this structure:

{{
  "title": "Lesson title",
  "introduction": "Short introduction",
  "sections": [
    {{
      "heading": "Section heading",
      "explanation": "Clear educational explanation"
    }}
  ],
  "summary": "Short summary"
}}

Rules:
- Use only the information provided about the concept.
- Do not invent unsupported facts.
- Make the explanation clear and educational.
- Keep it suitable for a short video.
- Return valid JSON only.
"""

    result = generate_text(prompt).strip()

    # Remove Markdown code fences if Ollama adds them
    result = re.sub(r"^```(?:json)?\s*", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s*```$", "", result).strip()

    # Extract the JSON object if the model added extra text
    start = result.find("{")
    end = result.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Ollama did not return a valid JSON object."
        )

    result = result[start:end + 1]

    # Remove invalid control characters inside the response
    result = "".join(
        char for char in result
        if char in "\n\r\t" or ord(char) >= 32
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON returned by Ollama: {e}"
        ) from e