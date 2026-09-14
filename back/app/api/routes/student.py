import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_student
from app.db.session import get_db
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.notification import Notification
from app.models.student_lesson_progress import StudentLessonProgress
from app.models.user import User


router = APIRouter(tags=["Student Dashboard"])


@router.post("/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_in_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    course = db.scalar(select(Course).where(Course.id == course_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.price > 0:
        raise HTTPException(status_code=402, detail="Paid course requires payment")

    enrollment = db.scalar(select(Enrollment).where(Enrollment.student_id == current_user.id, Enrollment.course_id == course_id))
    if enrollment is None:
        enrollment = Enrollment(student_id=current_user.id, course_id=course_id, source="free")
        db.add(enrollment)
        db.commit()

    return {"student_id": str(current_user.id), "course_id": str(course_id), "source": enrollment.source}


@router.get("/users/me/courses")
def my_courses(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.execute(select(Course, Enrollment).join(Enrollment, Enrollment.course_id == Course.id).where(Enrollment.student_id == current_user.id).order_by(Enrollment.enrolled_at.desc()).limit(limit)).all()
    return [{"id": str(course.id), "name": course.name, "description": course.description, "enrolled_at": enrollment.enrolled_at} for course, enrollment in rows]


@router.get("/users/me/courses/{course_id}/progress")
def course_progress(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrolled = db.scalar(select(Enrollment).where(Enrollment.student_id == current_user.id, Enrollment.course_id == course_id))
    if enrolled is None:
        raise HTTPException(status_code=403, detail="Course enrollment required")
    total = db.scalar(select(func.count(Lesson.id)).where(Lesson.course_id == course_id)) or 0
    completed = db.scalar(select(func.count(StudentLessonProgress.lesson_id)).join(Lesson, Lesson.id == StudentLessonProgress.lesson_id).where(StudentLessonProgress.student_id == current_user.id, Lesson.course_id == course_id, StudentLessonProgress.status == "completed")) or 0
    return {"course_id": str(course_id), "lessons_completed": completed, "lessons_total": total, "percent_complete": round(100 * completed / total, 1) if total else 0}


@router.post("/lessons/{lesson_id}/progress")
def update_lesson_progress(
    lesson_id: uuid.UUID,
    status_value: str = Query(..., alias="status", pattern="^(not_started|in_progress|completed)$"),
    video_watched_seconds: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    lesson = db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if lesson is None or lesson.course_id is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    enrolled = db.scalar(select(Enrollment).where(Enrollment.student_id == current_user.id, Enrollment.course_id == lesson.course_id))
    if enrolled is None:
        raise HTTPException(status_code=403, detail="Course enrollment required")
    progress = db.scalar(select(StudentLessonProgress).where(StudentLessonProgress.student_id == current_user.id, StudentLessonProgress.lesson_id == lesson_id))
    if progress is None:
        progress = StudentLessonProgress(student_id=current_user.id, lesson_id=lesson_id)
        db.add(progress)
    progress.status = status_value
    progress.video_watched_seconds = video_watched_seconds
    progress.completed_at = datetime.now(timezone.utc) if status_value == "completed" else None
    db.commit()
    return {"lesson_id": str(lesson_id), "status": progress.status, "video_watched_seconds": progress.video_watched_seconds}


@router.get("/users/me/notifications")
def my_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.scalars(select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(limit)).all()
    return rows


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "read"}


@router.get("/users/me/conversations")
def my_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(select(AIConversation).where(AIConversation.student_id == current_user.id).order_by(AIConversation.updated_at.desc()).limit(limit)).all()


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.scalar(select(AIConversation).where(AIConversation.id == conversation_id, AIConversation.student_id == current_user.id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.scalars(select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at)).all()
