
from pathlib import Path

path = Path("app/admin_learning_reset.py")
source = path.read_text(encoding="utf-8-sig")

import_line = "from app.learner_file_lock import learner_file_lock\n"

if import_line not in source:
    marker = "from pathlib import Path\n"
    if source.count(marker) != 1:
        raise SystemExit("STOP: Import location not found.")
    source = source.replace(marker, marker + import_line, 1)

start = source.find("def reset_learning_progress(")
if start == -1:
    raise SystemExit("STOP: Reset function not found.")

if "def _reset_learning_progress_unlocked(" in source:
    raise SystemExit("STOP: Lock wrapper already exists.")

source = source.replace(
    "def reset_learning_progress(",
    "def _reset_learning_progress_unlocked(",
    1,
)

wrapper = '''
def reset_learning_progress(
    learner_id: str,
    admin_id: str,
    learners_dir: str,
    auth_db_path: str,
):
    """Run an administrator reset under the learner's shared lock."""
    with learner_file_lock(learner_id):
        return _reset_learning_progress_unlocked(
            learner_id=learner_id,
            admin_id=admin_id,
            learners_dir=learners_dir,
            auth_db_path=auth_db_path,
        )
'''

source += "\n" + wrapper

compile(source, str(path), "exec")
path.write_text(source, encoding="utf-8")

print("ADMIN RESET LOCK INTEGRATION SUCCESSFUL")
