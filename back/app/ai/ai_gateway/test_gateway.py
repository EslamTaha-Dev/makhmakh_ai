from app.ai.ai_gateway.ai_gateway import ai_gateway_execute

try:
    res1 = ai_gateway_execute(task_type="chat", prompt="Say one word: Success")
    print("Chat Output:", res1)
except Exception as e:
    print("Chat Error:", e)

try:
    res2 = ai_gateway_execute(task_type="document_understanding", prompt="Summarize: Artificial Intelligence")
    print("Document Output:", res2)
except Exception as e:
    print("Document Error:", e)