
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app, require_user

client = TestClient(app)

admin_id = "aaaaaaaaaaaaaaaa"
learner_id = "bbbbbbbbbbbbbbbb"

fake_admin = SimpleNamespace(
    id=admin_id,
    role="admin",
)

app.dependency_overrides[require_user] = lambda: fake_admin

try:
    with patch(
        "app.main.reset_learning_progress",
        return_value={
            "success": True,
            "learner_id": learner_id,
            "message": "Mock reset completed",
        },
    ) as mock_reset:

        response = client.post(
            f"/admin/learners/{learner_id}/reset-progress",
            json={"confirmation": "RESET"},
        )

        print("Valid confirmation status:", response.status_code)

        assert response.status_code == 200
        assert response.json()["success"] is True

        mock_reset.assert_called_once_with(
            learner_id=learner_id,
            admin_id=admin_id,
            learners_dir=__import__(
                "app.main", fromlist=["LEARNERS_DIR"]
            ).LEARNERS_DIR,
            auth_db_path=__import__(
                "app.main", fromlist=["AUTH_DB_PATH"]
            ).AUTH_DB_PATH,
        )

        print("Administrator ID passed correctly: PASS")
        print("Selected learner ID passed correctly: PASS")
        print("Reset service called exactly once: PASS")
        print("ALL VALID CONFIRMATION TESTS PASSED")

finally:
    app.dependency_overrides.clear()
