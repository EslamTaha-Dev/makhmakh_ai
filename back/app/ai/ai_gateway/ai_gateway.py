from google import genai
from .key_pool import KeyPool
from .task_router import get_model_for_task

key_pool = KeyPool(cooldown_seconds=60)

key_pool.add_keys([
    ("API Key", "gemini"),
    ("API Key", "gemini"),
    ("API Key", "gemini"),
    ("API Key", "gemini"),
    ("API Key", "gemini"),
    ("API Key", "openrouter"),
])

def call_llm(model: str, prompt: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text

def ai_gateway_execute(task_type: str, prompt: str, provider: str = "gemini", max_retries: int = 5):
    model = get_model_for_task(task_type)

    for attempt in range(max_retries):
        api_key = key_pool.reserve_key(target_provider=provider)

        try:
            result = call_llm(model=model, prompt=prompt, api_key=api_key)
            return result

        except Exception as e:
            error_msg = str(e).lower()
            
            if "401" in error_msg or "403" in error_msg or "unauthenticated" in error_msg or "permission" in error_msg or "not valid" in error_msg:
                key_pool.disable_key(api_key)
            elif "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
                key_pool.set_cooldown(api_key)
            else:
                raise e

    raise Exception("All keys in pool failed.")