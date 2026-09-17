from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.admin_audit_log import AdminAuditLog
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.payment import Payment
from app.payments.service import apply_payment_status, get_payment_provider
from app.payments.types import PaymentStatus
from app.core.pagination import decode_cursor, encode_cursor
from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


ADMIN_ROLES = ("admin", "super_admin")

ALLOWED_ROLES = {
    "student",
    "instructor",
    "content_creator",
    "support",
    "admin",
    "super_admin",
}


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(
        min_length=1,
        max_length=50,
    )


@router.get("/users")
def list_users(
    response: Response,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ADMIN_ROLES)
    ),
):
    statement = select(User).order_by(User.created_at.desc(), User.id.desc())
    decoded = decode_cursor(cursor)
    if cursor and decoded is None:
        raise HTTPException(status_code=400, detail="Invalid cursor")
    if decoded:
        created_at, item_id = decoded
        statement = statement.where(
            (User.created_at < created_at)
            | ((User.created_at == created_at) & (User.id < item_id))
        )
    users = db.scalars(statement.limit(limit + 1)).all()
    if len(users) > limit:
        next_user = users.pop()
        response.headers["X-Next-Cursor"] = encode_cursor(next_user.created_at, next_user.id)

    return [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: UUID,
    data: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ADMIN_ROLES)
    ),
):
    new_role = data.role.strip().lower()

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if (
        user.role == "super_admin"
        and current_user.role != "super_admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only super_admin can modify a super_admin",
        )
    if (
        new_role == "super_admin"
        and current_user.role != "super_admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only super_admin can assign super_admin role",
        )
    if user.id == current_user.id and new_role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own admin privileges",
        )

    role = db.scalar(
        select(Role).where(Role.name == new_role)
    )

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )

    user.role = new_role
    db.execute(
        delete(UserRole).where(
            UserRole.user_id == user.id
        )
    )
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": str(user.id),
        "role": user.role,
    }


@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    return {
        "students": db.scalar(select(func.count(User.id)).where(User.role == "student")) or 0,
        "courses": db.scalar(select(func.count(Course.id))) or 0,
        "enrollments": db.scalar(select(func.count()).select_from(Enrollment)) or 0,
    }


@router.get("/students")
def admin_students(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    limit = max(1, min(limit, 100))
    students = db.scalars(select(User).where(User.role == "student").order_by(User.created_at.desc()).limit(limit)).all()
    return [{"id": str(user.id), "name": user.name, "email": user.email, "created_at": user.created_at} for user in students]


@router.get("/students/{student_id}/progress")
def admin_student_progress(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    student = db.scalar(select(User).where(User.id == student_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"student_id": str(student_id), "concept_progress": [{"concept_id": str(row.concept_id), "status": row.status} for row in student.progress]}


@router.get("/audit-logs")
def admin_audit_logs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin")),
):
    limit = max(1, min(limit, 100))
    return db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit)).all()


@router.get("/payments")
def admin_payments(
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    statement = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    if status_filter:
        statement = statement.where(Payment.status == status_filter)
    payments = db.scalars(statement).all()
    return [
        {
            "id": str(payment.id),
            "user_id": str(payment.user_id),
            "course_id": str(payment.course_id),
            "provider": payment.provider,
            "status": payment.status,
            "amount": str(payment.amount),
            "created_at": payment.created_at,
        }
        for payment in payments
    ]


@router.post("/payments/{payment_id}/refund")
def admin_refund_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    payment = db.scalar(select(Payment).where(Payment.id == payment_id))
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != PaymentStatus.PAID.value:
        raise HTTPException(status_code=409, detail="Only paid payments can be refunded")
    if not payment.external_id:
        raise HTTPException(status_code=409, detail="Payment has no provider reference")

    provider = get_payment_provider(payment.provider)
    if not provider.refund_payment(payment.external_id, payment.amount):
        raise HTTPException(status_code=502, detail="Payment provider rejected refund")

    apply_payment_status(db, payment, PaymentStatus.REFUNDED)
    return {"payment_id": str(payment.id), "status": payment.status}


@router.get("/conversations/{conversation_id}")
def admin_view_conversation(
    conversation_id: UUID,
    reason: str = Query(..., min_length=5, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN_ROLES)),
):
    conversation = db.scalar(select(AIConversation).where(AIConversation.id == conversation_id))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.add(AdminAuditLog(
        admin_id=current_user.id,
        action="view_student_conversation",
        resource_type="conversation",
        resource_id=str(conversation_id),
        details={"reason": reason, "student_id": str(conversation.student_id)},
    ))
    db.commit()

    messages = db.scalars(select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.created_at)).all()
    return {
        "conversation": conversation,
        "messages": messages,
    }