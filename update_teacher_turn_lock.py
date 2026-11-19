
from pathlib import Path

path = Path("app/main.py")
source = path.read_text(encoding="utf-8-sig")

import_line = "from app.learner_file_lock import learner_file_lock\n"
marker = "from app.agents.autonomous_teacher import teacher_step\n"

if import_line not in source:
    if source.count(marker) != 1:
        raise SystemExit("STOP: Teacher import not found exactly once.")
    source = source.replace(marker, marker + import_line, 1)

start_marker = '@app.post("/teacher-agent/turn")\n'
end_marker = '@app.post("/teacher-agent/extract")'

if source.count(start_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit("STOP: Teaching endpoint boundaries not found.")

start = source.index(start_marker)
end = source.index(end_marker, start)

section = source[start:end]

if "with learner_file_lock(req.learner_id):" in section:
    raise SystemExit("STOP: Teaching endpoint is already locked.")

lines = section.splitlines(keepends=True)

function_line = next(
    (i for i, line in enumerate(lines)
     if line.startswith("def teacher_agent_turn(")),
    None,
)

if function_line is None:
    raise SystemExit("STOP: Teacher function not found.")

body_start = function_line + 1

if not lines[body_start].lstrip().startswith(
    "require_learner_access("
):
    raise SystemExit("STOP: Unexpected teaching endpoint structure.")

# Keep authorization outside the lock.
authorization_line = lines[body_start]

body = lines[body_start + 1:]

new_section = (
    "".join(lines[:body_start])
    + authorization_line
    + "    with learner_file_lock(req.learner_id):\n"
    + "".join("    " + line if line.strip() else line for line in body)
)

updated = source[:start] + new_section + source[end:]

compile(updated, str(path), "exec")
path.write_text(updated, encoding="utf-8")

print("TEACHING ENDPOINT LOCK INTEGRATION SUCCESSFUL")
