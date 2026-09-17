import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.core.rate_limit import limiter
from app.models.chat import ChatMessage, ChatSession
from app.models.course import Course
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)
from app.models.ai_interaction import AIInteraction
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.student_node_mastery import StudentNodeMastery
from app.services.agent_service import run_agent

from app.ai.ai_gateway.ai_gateway import AIGatewayError, ai_gateway_execute

router = APIRouter(
    tags=["Chat"],
)


@limiter.limit("20/minute")
@router.post(
    "/courses/{course_id}/chat",
    response_model=ChatResponse,
)
def chat(
    request: Request,
    course_id: uuid.UUID,
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.scalar(select(Course).where(Course.id == course_id))

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if data.session_id:
        session = db.scalar(
            select(ChatSession).where(
                ChatSession.id == data.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.course_id == course_id,
            )
        )

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

    else:
        session = ChatSession(
            user_id=current_user.id,
            course_id=course_id,
        )

        db.add(session)
        db.flush()

    session_id = session.id

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.message,
        sources=[],
    )

    db.add(user_message)
    db.flush()

    try:
        result = run_agent(
            db=db,
            user_id=current_user.id,
            course_id=str(course_id),
            question=data.message,
            node_id=data.node_id,
        )

    except AIGatewayError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is not available right now.",
        ) from exc

    except Exception:
        db.rollback()

        try:
            gateway_answer = ai_gateway_execute(
                task_type="chat",
                prompt=data.message,
            )
        except AIGatewayError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI assistant is not available right now.",
            ) from exc

        result = {
            "answer": gateway_answer,
            "tool_result": {},
            "tool_name": None,
            "model": "gemini-3.6-flash",
            "fallback_mode": "direct",
        }

    answer = result.get(
        "answer",
        "I could not generate an answer.",
    )

    tool_result = result.get(
        "tool_result",
        {},
    )

    tool_name = result.get(
        "tool_name",
    )

    conversation = db.scalar(
        select(AIConversation)
        .where(
            AIConversation.student_id == current_user.id,
            AIConversation.course_id == course_id,
        )
        .order_by(AIConversation.updated_at.desc())
    )

    if conversation is None:
        conversation = AIConversation(
            student_id=current_user.id,
            course_id=course_id,
            title=data.message[:255],
        )
        db.add(conversation)
        db.flush()

    db.add(
        AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=data.message,
        )
    )

    sources = []

    if tool_name == "search_course_content":
        search_results = tool_result.get(
            "results",
            [],
        )

        sources = [
            {
                "chunk_id": item.get("chunk_id"),
                "material_id": item.get("material_id"),
                "file_name": item.get("file_name"),
                "text": item.get("text"),
                "distance": item.get("distance"),
            }
            for item in search_results
        ]

    if data.node_id:
        mastery = db.scalar(
            select(StudentNodeMastery).where(
                StudentNodeMastery.student_id == current_user.id,
                StudentNodeMastery.node_id == data.node_id,
            )
        )
        if mastery is None:
            mastery = StudentNodeMastery(
                student_id=current_user.id,
                node_id=data.node_id,
            )
            db.add(mastery)
        mastery.times_asked_about += 1
        mastery.status = (
            "needs_review" if mastery.times_asked_about >= 3 else "in_progress"
        )
        mastery.last_interacted_at = datetime.utcnow()

    ai_interaction = AIInteraction(
        user_id=current_user.id,
        course_id=course_id,
        question=data.message,
        tools_used=[tool_name] if tool_name else [],
        retrieved_chunks=(
            tool_result.get("results", [])
            if tool_name == "search_course_content"
            else []
        ),
        answer=answer,
        sources=sources,
        conversation_id=conversation.id,
        node_id=data.node_id,
        model=result.get("model"),
        latency_ms=result.get("latency_ms"),
        tokens=None,
        feedback=None,
        rag_pipeline_version=result.get("fallback_mode", "unknown"),
    )

    db.add(ai_interaction)

    db.add(
        AIMessage(
            conversation_id=conversation.id,
            interaction=ai_interaction,
            role="assistant",
            content=answer,
        )
    )

    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources=sources,
    )

    db.add(assistant_message)

    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_message.id,
        answer=assistant_message.content,
        sources=sources,
    )


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_chat_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    return messages
