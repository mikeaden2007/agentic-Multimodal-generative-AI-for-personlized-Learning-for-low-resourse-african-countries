
import json
import sqlite3
import tempfile
from pathlib import Path

from app.admin_learning_reset import (
    LearningResetError,
    reset_learning_progress,
)

ADMIN_ID = "aaaaaaaaaaaaaaaa"
STUDENT_ID = "bbbbbbbbbbbbbbbb"
OTHER_ID = "cccccccccccccccc"

with tempfile.TemporaryDirectory(prefix="asktutor_reset_test_") as tmp:
    root = Path(tmp)
    learners = root / "learners"
    learners.mkdir()

    database = root / "users.db"

    
    conn = sqlite3.connect(database)

    try:
        conn.execute(
            "CREATE TABLE users (id TEXT PRIMARY KEY, role TEXT NOT NULL)"
        )

        conn.executemany(
            "INSERT INTO users (id, role) VALUES (?, ?)",
            [
                (ADMIN_ID, "admin"),
                (STUDENT_ID, "student"),
                (OTHER_ID, "student"),
            ],
        )

        conn.commit()

    finally:
        conn.close()

    def make_record(learner_id):
        return {
            "learner_id": learner_id,
            "teacher_topic_progress": {
                "English Language": {"Grammar": {"completed": True}},
                "Mathematics": {"Fractions": {"completed": True}},
                "Biology": {"Cells": {"completed": True}},
                "General Mathematics": {"Algebra": {"completed": True}},
            },
            "teacher_subject_sessions": {
                "English Language": {"phase": "practice"},
                "Mathematics": {"phase": "practice"},
                "Biology": {"phase": "practice"},
                "General Mathematics": {"phase": "practice"},
            },
            "teacher_session": {"phase": "practice"},
            "mastery": {"Fractions": 0.8},
            "assessment_history": [{"topic": "Fractions", "score": 80}],
            "history": [{"question": "What is a fraction?"}],
            "study_history": [{"subject": "Mathematics"}],
            "agent_plans": {"Mathematics::Fractions": {"status": "accepted"}},
            "agent_decisions": [{"action": "targeted_practice"}],
        }

    selected = make_record(STUDENT_ID)
    other = make_record(OTHER_ID)

    selected_path = learners / f"{STUDENT_ID}.json"
    other_path = learners / f"{OTHER_ID}.json"

    selected_path.write_text(json.dumps(selected), encoding="utf-8")
    other_path.write_text(json.dumps(other), encoding="utf-8")

    other_before = other_path.read_bytes()

    # Unauthorized users must not be able to reset progress.
    try:
        reset_learning_progress(
            STUDENT_ID, OTHER_ID, str(learners), str(database)
        )
        raise AssertionError("Student was allowed to reset progress")
    except LearningResetError:
        print("Non-admin reset denied: PASS")

    assert selected_path.read_bytes() == json.dumps(selected).encode("utf-8")

    result = reset_learning_progress(
        STUDENT_ID, ADMIN_ID, str(learners), str(database)
    )

    assert result["success"] is True

    after = json.loads(selected_path.read_text(encoding="utf-8"))

    for subject in (
        "English Language",
        "Mathematics",
        "Biology",
        "General Mathematics",
    ):
        assert after["teacher_topic_progress"][subject] == {}
        assert after["teacher_subject_sessions"][subject]["phase"] == "intro"

    print("Selected teaching progress reset: PASS")

    for field in (
        "mastery",
        "assessment_history",
        "history",
        "study_history",
        "agent_plans",
        "agent_decisions",
    ):
        assert after[field] == selected[field], field

    print("Other learning data preserved: PASS")

    assert other_path.read_bytes() == other_before
    print("Other learner unchanged: PASS")

    backup_dir = root / "learner_reset_backups"
    backups = list(backup_dir.glob(f"{STUDENT_ID}_*.json"))

    assert len(backups) == 1
    assert json.loads(backups[0].read_text(encoding="utf-8")) == selected

    print("Original backup verified: PASS")

    audit_path = backup_dir / "admin_reset_audit.jsonl"
    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]

    assert [event["status"] for event in events] == [
        "prepared",
        "completed",
    ]

    assert events[0]["operation_id"] == events[1]["operation_id"]

    print("Audit preparation and completion: PASS")
    print("ALL ISOLATED RESET TESTS PASSED")
