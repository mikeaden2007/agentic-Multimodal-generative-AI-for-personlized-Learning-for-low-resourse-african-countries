
from pathlib import Path
import ast

path = Path("app/main.py")
source = path.read_text(encoding="utf-8")

if '@app.get("/admin/students")' in source:
    raise RuntimeError("Administrator API already exists.")

import_marker = "from app.auth import AuthStore, AuthError"

if import_marker not in source:
    raise RuntimeError("Authentication import not found.")

source = source.replace(
    import_marker,
    import_marker
    + "\nimport sqlite3"
    + "\nfrom app.admin_learning_reset import "
    + "LearningResetError, reset_learning_progress",
    1,
)

admin_api = '''

# ---------- Administrator-only learner management ----------

class AdminResetRequest(BaseModel):
    confirmation: str


@app.get("/admin/students")
def admin_list_students(user=Depends(require_role("admin"))):
    """Return student accounts without authentication secrets."""
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT id, name, email, country,
                   class_level, stream, created_at
            FROM users
            WHERE role = 'student'
            ORDER BY name COLLATE NOCASE, id
            """
        ).fetchall()
        students = [dict(row) for row in rows]
    finally:
        conn.close()

    return {
        "students": students,
        "total": len(students),
    }


@app.post("/admin/learners/{learner_id}/reset-progress")
def admin_reset_student_progress(
    learner_id: str,
    req: AdminResetRequest,
    user=Depends(require_role("admin")),
):
    """Reset teaching progress only after administrator confirmation."""
    if req.confirmation != "RESET":
        raise HTTPException(
            status_code=400,
            detail="Type RESET to confirm this operation.",
        )

    try:
        result = reset_learning_progress(
            learner_id=learner_id,
            admin_id=user.id,
            learners_dir=LEARNERS_DIR,
            auth_db_path=AUTH_DB_PATH,
        )
    except LearningResetError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return result


'''

# Append endpoints after the existing application definitions.
updated = source.rstrip() + "\n" + admin_api

ast.parse(updated)

path.write_text(updated, encoding="utf-8")

print("ADMINISTRATOR API ADDED")
print("GET /admin/students")
print("POST /admin/learners/{learner_id}/reset-progress")
print("Administrator role protection: ENABLED")
print("Explicit RESET confirmation: ENABLED")
print("Python syntax: VERIFIED")
