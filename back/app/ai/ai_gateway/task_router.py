TASK_MODEL_MAPPING = {
    "document_understanding": "gemini-3.6-flash",
    "chat": "gemini-3.6-flash",
    "video_script": "gemini-3.6-flash",
    "study_plan": "gemini-3.6-flash"
}

def get_model_for_task(task_type: str) -> str:
    return TASK_MODEL_MAPPING.get(task_type, "gemini-3.6-flash")