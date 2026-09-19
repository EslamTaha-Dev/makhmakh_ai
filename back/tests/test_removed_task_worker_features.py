from app.main import app
from app.schemas.auth import UserResponse
from app.schemas.course import CourseCreate, CourseResponse


REMOVED_ROUTES = {
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/verify-email",
    "/api/v1/admin/payments",
    "/api/v1/payments",
    "/api/v1/payments/webhooks/paymob",
    "/api/v1/payments/webhooks/fawry",
}


def test_task_worker_routes_are_not_published() -> None:
    published_paths = set(app.openapi()["paths"])

    assert published_paths.isdisjoint(REMOVED_ROUTES)
    assert not any(path.startswith("/api/v1/payments/") for path in published_paths)


def test_registration_and_course_contracts_exclude_removed_fields() -> None:
    register_schema = (
        app.openapi()["paths"]["/api/v1/auth/register"]["post"]["responses"]["201"]
        ["content"]["application/json"]["schema"]
    )

    assert register_schema["$ref"].endswith("/UserResponse")
    assert "verification_token" not in UserResponse.model_fields
    assert "price" not in CourseCreate.model_fields
    assert "price" not in CourseResponse.model_fields
