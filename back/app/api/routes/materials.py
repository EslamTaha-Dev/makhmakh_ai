import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_user_roles,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.material import Material
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.material import MaterialResponse
from app.services.material_processor import process_material
from app.services.queue import enqueue_job, processing_queue


router = APIRouter(
    prefix="/courses",
    tags=["Materials"],
)


settings = get_settings()


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".ppt",
    ".txt",
    ".docx",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
}


CONTENT_MANAGEMENT_ROLES = (
    "instructor",
    "content_creator",
    "admin",
    "super_admin",
)

ADMIN_ROLES = {
    "admin",
    "super_admin",
}

PUBLIC_VISIBILITY = "public"

CHUNK_SIZE = 1024 * 1024


def can_contribute_material(
    course: Course,
    user: User,
) -> bool:
    """Decide who may attach material to a course.

    A course owner can always upload into their own space (this is how a student
    builds a personal corpus). Staff can additionally contribute to the shared
    public catalog.
    """

    if course.created_by == user.id:
        return True

    user_roles = get_user_roles(user)

    if user_roles.intersection(ADMIN_ROLES):
        return True

    return (
        bool(user_roles.intersection(CONTENT_MANAGEMENT_ROLES))
        and course.visibility == PUBLIC_VISIBILITY
    )


def validate_file_signature(
    extension: str,
    header: bytes,
) -> bool:
    if extension == ".pdf":
        return header.startswith(b"%PDF-")

    if extension in {".docx", ".pptx"}:
        return header.startswith(b"PK\x03\x04")

    if extension == ".ppt":
        return header.startswith(b"\xD0\xCF\x11\xE0")

    if extension == ".mp3":
        return (
            header.startswith(b"ID3")
            or (
                len(header) >= 2
                and header[0] == 0xFF
                and (header[1] & 0xE0) == 0xE0
            )
        )

    if extension == ".wav":
        return (
            len(header) >= 12
            and header[0:4] == b"RIFF"
            and header[8:12] == b"WAVE"
        )

    if extension in {".mp4", ".mov"}:
        return (
            len(header) >= 12
            and header[4:8] == b"ftyp"
        )

    if extension == ".txt":
        return True

    return False


def read_initial_bytes(file: UploadFile) -> bytes:
    position = file.file.tell()

    try:
        file.file.seek(0)
        return file.file.read(8192)
    finally:
        file.file.seek(position)


@router.post(
    "/{course_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_material(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
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

    if not can_contribute_material(course, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only upload materials to courses you created"
            ),
        )

    original_name = Path(
        file.filename or "unknown"
    ).name

    if not original_name or original_name == ".":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name",
        )

    extension = Path(
        original_name
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    initial_bytes = read_initial_bytes(file)

    if not initial_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if not validate_file_signature(
        extension,
        initial_bytes,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the declared file type",
        )

    max_upload_size = (
        settings.upload_max_size_mb
        * 1024
        * 1024
    )

    upload_dir = Path(
        settings.upload_dir
    ).resolve()

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    material_id = uuid.uuid4()

    safe_filename = (
        f"{material_id}{extension}"
    )

    file_path = (
        upload_dir
        / safe_filename
    )

    total_size = 0

    try:
        file.file.seek(0)

        with file_path.open("xb") as buffer:
            while True:
                chunk = file.file.read(
                    CHUNK_SIZE
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_upload_size:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            f"File is too large. "
                            f"Maximum allowed size is "
                            f"{settings.upload_max_size_mb} MB"
                        ),
                    )

                buffer.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        material = Material(
            id=material_id,
            course_id=course_id,
            uploaded_by=current_user.id,
            file_name=original_name,
            file_type=extension.lstrip("."),
            storage_url=str(file_path),
            processing_status="pending",
        )

        db.add(material)

        job = ProcessingJob(
            material_id=material_id,
            job_type="material_processing",
            status="pending",
        )

        db.add(job)

        db.commit()
        db.refresh(material)

        enqueue_job(
            processing_queue,
            process_material,
            str(material_id),
        )

        return material

    except HTTPException:
        file_path.unlink(
            missing_ok=True
        )

        db.rollback()

        raise

    except Exception:
        file_path.unlink(
            missing_ok=True
        )

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload material",
        )

    finally:
        file.file.close()


@router.get(
    "/materials/{material_id}",
    response_model=MaterialResponse,
)
def get_material(
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.scalar(
        select(Material).where(
            Material.id == material_id
        )
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    if material.uploaded_by != current_user.id:
        course = db.scalar(
            select(Course).where(Course.id == material.course_id)
        )

        if course is None or not can_contribute_material(course, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this material",
            )

    return material


@router.get(
    "/{course_id}/materials",
    response_model=list[MaterialResponse],
)
def list_course_materials(
    course_id: uuid.UUID,
    response: Response,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.scalar(
        select(Course).where(Course.id == course_id)
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    if not can_contribute_material(course, current_user):
        user_roles = get_user_roles(current_user)

        is_enrolled = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course_id,
            )
        )

        can_read = (
            course.visibility == PUBLIC_VISIBILITY
            or bool(user_roles.intersection(ADMIN_ROLES))
            or is_enrolled is not None
        )

        if not can_read:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

    materials = db.scalars(
        select(Material)
        .where(Material.course_id == course_id)
        .order_by(Material.uploaded_at.desc())
        .limit(limit)
    ).all()

    response.headers["X-Total-Count"] = str(len(materials))

    return materials