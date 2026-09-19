import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_user_roles,
    require_admin,
)
from app.db.session import get_db
from app.models.concept import Concept
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.concept import ConceptResponse
from app.schemas.course import CourseCreate, CourseResponse
from app.core.pagination import decode_cursor, encode_cursor


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


PUBLIC_VISIBILITY = "public"
PRIVATE_VISIBILITY = "private"

CONTENT_PUBLISHING_ROLES = (
    "instructor",
    "content_creator",
    "admin",
    "super_admin",
)

ADMIN_ROLES = {
    "admin",
    "super_admin",
}


def course_visibility_allows_read(
    course: Course,
    user: User,
) -> bool:
    """Public courses are readable by everyone; private ones only by their owner."""

    if course.visibility == PUBLIC_VISIBILITY:
        return True

    if course.created_by == user.id:
        return True

    return bool(get_user_roles(user).intersection(ADMIN_ROLES))


@router.get(
    "",
    response_model=list[CourseResponse],
)
def list_courses(
    response: Response,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Course)
        .where(Course.visibility == PUBLIC_VISIBILITY)
        .order_by(Course.created_at.desc(), Course.id.desc())
    )
    decoded = decode_cursor(cursor)
    if cursor and decoded is None:
        raise HTTPException(status_code=400, detail="Invalid cursor")
    if decoded:
        created_at, item_id = decoded
        statement = statement.where(
            (Course.created_at < created_at)
            | ((Course.created_at == created_at) & (Course.id < item_id))
        )
    courses = db.scalars(statement.limit(limit + 1)).all()
    if len(courses) > limit:
        next_course = courses.pop()
        response.headers["X-Next-Cursor"] = encode_cursor(next_course.created_at, next_course.id)

    return courses


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a course.

    Instructors and admins publish into the shared catalog. Students get a private
    study space, which is where they upload their own lecture material — the corpus
    stays scoped to them.
    """

    user_roles = get_user_roles(current_user)

    can_publish = bool(
        user_roles.intersection(CONTENT_PUBLISHING_ROLES)
    )

    visibility = (
        PUBLIC_VISIBILITY if can_publish else PRIVATE_VISIBILITY
    )

    course = Course(
        name=data.name.strip(),
        description=data.description,
        visibility=visibility,
        created_by=current_user.id,
    )

    db.add(course)
    db.flush()

    existing_enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course.id,
        )
    )

    if existing_enrollment is None:
        db.add(
            Enrollment(
                student_id=current_user.id,
                course_id=course.id,
                source="owner",
            )
        )

    db.commit()
    db.refresh(course)

    return course


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: uuid.UUID,
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

    if not course_visibility_allows_read(course, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course


@router.get(
    "/{course_id}/concepts",
    response_model=list[ConceptResponse],
)
def list_course_concepts(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Concepts extracted from the course material, in study order."""

    course = db.scalar(
        select(Course).where(Course.id == course_id)
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if not course_visibility_allows_read(course, current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return db.scalars(
        select(Concept)
        .where(Concept.course_id == course_id)
        .order_by(Concept.order_index, Concept.created_at)
    ).all()


@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: uuid.UUID,
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    course = db.scalar(select(Course).where(Course.id == course_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    course.name = data.name.strip()
    course.description = data.description
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    course = db.scalar(select(Course).where(Course.id == course_id))
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
