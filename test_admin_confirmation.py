
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app, require_user

client = TestClient(app)

fake_admin = SimpleNamespace(
    id="aaaaaaaaaaaaaaaa",
    role="admin",
)

app.dependency_overrides[require_user] = lambda: fake_admin

try:
    response = client.get("/admin/students")

    print("Administrator student list:", response.status_code)
    assert response.status_code == 200
    assert "students" in response.json()

    with patch(
        "app.main.reset_learning_progress"
    ) as mock_reset:

        learner_id = "bbbbbbbbbbbbbbbb"

        for confirmation in ("", "YES", "reset", "CONFIRM"):
            response = client.post(
                f"/admin/learners/{learner_id}/reset-progress",
                json={"confirmation": confirmation},
            )

            assert response.status_code == 400

        response = client.post(
            f"/admin/learners/{learner_id}/reset-progress",
            json={},
        )

        assert response.status_code == 422
        mock_reset.assert_not_called()

    print("Invalid confirmations rejected: PASS")
    print("Missing confirmation rejected: PASS")
    print("Reset service never invoked: PASS")
    print("ALL ADMINISTRATOR CONFIRMATION TESTS PASSED")

finally:
    app.dependency_overrides.clear()
