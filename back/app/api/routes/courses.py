import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse
from app.core.pagination import decode_cursor, encode_cursor


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


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
    statement = select(Course).order_by(Course.created_at.desc(), Course.id.desc())
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
    current_user: User = Depends(require_admin),
):
    course = Course(
        name=data.name.strip(),
        description=data.description,
        price=data.price,
        created_by=current_user.id,
    )

    db.add(course)
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

    return course


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
    course.price = data.price
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