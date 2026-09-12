import uuid

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
from app.services.rag_chat import answer_question


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
    course = db.scalar(
        select(Course).where(
            Course.id == course_id
        )
    )

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

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=data.message,
        sources=[],
    )

    db.add(user_message)
    db.flush()

    try:
        result = answer_question(
            course_id=str(course_id),
            question=data.message,
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer",
        ) from exc

    answer = result.get(
        "answer",
        "I could not generate an answer.",
    )

    sources = result.get(
        "sources",
        [],
    )

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        sources=sources,
    )

    db.add(assistant_message)

    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        session_id=session.id,
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
        .where(
            ChatMessage.session_id == session_id
        )
        .order_by(ChatMessage.created_at)
    ).all()

    return messages