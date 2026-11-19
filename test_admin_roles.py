
from types import SimpleNamespace

from fastapi.testclient import TestClient
from app.main import app, require_user

client = TestClient(app)

student_id = "0000000000000000"

for role in ("student", "teacher", "parent"):
    fake_user = SimpleNamespace(
        id="1111111111111111",
        role=role,
    )

    app.dependency_overrides[require_user] = (
        lambda user=fake_user: user
    )

    try:
        listing = client.get("/admin/students")

        reset = client.post(
            f"/admin/learners/{student_id}/reset-progress",
            json={"confirmation": "RESET"},
        )

        print(
            f"{role}: list={listing.status_code}, "
            f"reset={reset.status_code}"
        )

        assert listing.status_code == 403
        assert reset.status_code == 403

    finally:
        app.dependency_overrides.clear()

print("ALL NON-ADMINISTRATOR ROLES DENIED: PASS")
