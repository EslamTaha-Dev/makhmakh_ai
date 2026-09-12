import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.course import Course
from app.models.material import Material
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.material import MaterialResponse
from app.services.material_processor import process_material
from app.services.queue import processing_queue


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


@router.post(
    "/{course_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_material(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*CONTENT_MANAGEMENT_ROLES)
    ),
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

    original_name = file.filename or "unknown"

    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    upload_dir = Path(settings.upload_dir)

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    material_id = uuid.uuid4()

    safe_filename = f"{material_id}{extension}"

    file_path = upload_dir / safe_filename

    with file_path.open("wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)

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

    processing_queue.enqueue(
        process_material,
        str(material.id),
    )

    return material


@router.get(
    "/materials/{material_id}",
    response_model=MaterialResponse,
)
def get_material(
    material_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*CONTENT_MANAGEMENT_ROLES)
    ),
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

    return material