
from pathlib import Path
import ast

path = Path("app/admin_learning_reset.py")
source = path.read_text(encoding="utf-8")

start_marker = "    temporary_path = None\n"
end_marker = "\n    return {\n"

start = source.find(start_marker)
end = source.find(end_marker, start)

if start == -1 or end == -1:
    raise RuntimeError(
        "Expected reset section not found. No changes made."
    )

if "def _append_reset_audit(" in source:
    raise RuntimeError(
        "Audit helper already installed. No changes made."
    )

helper = '''
def _append_reset_audit(audit_path, event):
    """Append an audit event and synchronize it to disk."""
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\\\\n")
        handle.flush()
        os.fsync(handle.fileno())


'''

# Add the helper before the reset implementation.
function_marker = "def _reset_learning_progress_unlocked("
if function_marker not in source:
    raise RuntimeError("Reset implementation not found.")

source = source.replace(
    function_marker,
    helper + function_marker,
    1,
)

# Locate the reset section again after inserting the helper.
start = source.find(start_marker)
end = source.find(end_marker, start)

replacement = '''    audit_path = backup_dir / "admin_reset_audit.jsonl"
    operation_id = f"{learner_id}_{timestamp}"

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operation_id": operation_id,
        "administrator_id": admin_id,
        "learner_id": learner_id,
        "action": "reset_autonomous_teacher_progress",
        "subjects": list(subjects),
        "backup_file": backup.name,
        "original_sha256": original_hash,
    }

    # A durable preparation record must exist before changing progress.
    try:
        _append_reset_audit(
            audit_path,
            {**event, "status": "prepared"},
        )
    except Exception as exc:
        raise LearningResetError(
            "Could not record reset preparation. "
            "Learner progress was not changed."
        ) from exc

    temporary_path = None
    replaced = False

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=f".{learner_id}_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(updated, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, target)
        temporary_path = None
        replaced = True

        _append_reset_audit(
            audit_path,
            {
                **event,
                "status": "completed",
                "timestamp_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
        )

    except Exception as exc:
        # Preserve the verified backup for investigation/recovery.
        try:
            _append_reset_audit(
                audit_path,
                {
                    **event,
                    "status": (
                        "completion_unconfirmed"
                        if replaced else "failed"
                    ),
                    "timestamp_utc": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "error_type": type(exc).__name__,
                },
            )
        except Exception:
            pass

        if replaced:
            raise LearningResetError(
                "The reset file was replaced, but completion "
                "logging failed. The verified backup remains "
                "available. Administrator review is required."
            ) from exc

        raise LearningResetError(
            "Reset failed before replacing learner progress. "
            "The original record remains available."
        ) from exc

    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
'''

updated = source[:start] + replacement + source[end:]

ast.parse(updated)

path.write_text(updated, encoding="utf-8")

print("ADMIN RESET AUDIT SAFEGUARDS UPDATED")
print("Pre-reset audit: ENABLED")
print("Durable audit writes: ENABLED")
print("Completion and failure events: ENABLED")
print("Python syntax: VERIFIED")
