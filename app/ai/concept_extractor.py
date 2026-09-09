from app.ai.ollama_client import generate_json
SYSTEM_PROMPT = """
You are an educational concept extraction system.

Extract only the main concepts explicitly present in the provided text.

Rules:
1. Do not invent information.
2. Return at most 5 concepts.
3. Keep concept names short.
4. Keep descriptions short.
5. Add prerequisites only when clearly supported by the text.
6. Return ONLY valid JSON.
"""


def extract_concepts(text: str) -> dict:
    text = text.strip()[:6000]

    if not text:
        return {
            "concepts": [],
            "prerequisites": [],
        }

    prompt = f"""
Extract the main educational concepts from this course text.

Return ONLY this JSON structure:

{{
  "concepts": [
    {{
      "name": "Concept name",
      "description": "Short description",
      "order_index": 0
    }}
  ],
  "prerequisites": [
    {{
      "concept": "Advanced concept",
      "prerequisite": "Required concept"
    }}
  ]
}}

TEXT:
{text}
"""

    result = generate_json(
        prompt=prompt,
        system=SYSTEM_PROMPT,
    )

    if not isinstance(result, dict):
        return {
            "concepts": [],
            "prerequisites": [],
        }

    concepts = result.get("concepts")

    if not isinstance(concepts, list):
        result["concepts"] = []

    prerequisites = result.get("prerequisites")

    if not isinstance(prerequisites, list):
        result["prerequisites"] = []

    return result