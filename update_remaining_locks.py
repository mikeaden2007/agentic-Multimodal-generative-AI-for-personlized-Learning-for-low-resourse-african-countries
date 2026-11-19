
from pathlib import Path
import ast
import textwrap

path = Path("app/main.py")
source = path.read_text(encoding="utf-8")

functions = {
    "ask",
    "practice_submit",
    "objective_submit",
    "record_study",
    "update_agent_plan",
}

tree = ast.parse(source)
lines = source.splitlines(keepends=True)

changes = []

for node in tree.body:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue

    if node.name not in functions:
        continue

    if not node.body:
        raise RuntimeError(f"Empty function: {node.name}")

    # The access check must remain outside the lock.
    first = node.body[0]
    first_code = "".join(
        lines[first.lineno - 1:first.end_lineno]
    )

    if "require_learner_access(" not in first_code:
        raise RuntimeError(
            f"Unexpected function structure: {node.name}"
        )

    if len(node.body) < 2:
        raise RuntimeError(
            f"Missing endpoint body: {node.name}"
        )

    start = node.body[1].lineno - 1
    end = node.end_lineno

    original = "".join(lines[start:end])

    if "with learner_file_lock(" in original:
        raise RuntimeError(
            f"Already locked: {node.name}"
        )

    # AST line ranges can include nested code. Preserve it.
    wrapped = (
        "    with learner_file_lock(req.learner_id):\n"
        + textwrap.indent(original, "    ")
    )

    changes.append((start, end, wrapped, node.name))

found = {name for _, _, _, name in changes}

if found != functions:
    raise RuntimeError(
        f"Expected {sorted(functions)}, found {sorted(found)}"
    )

if "from app.learner_file_lock import learner_file_lock" not in source:
    raise RuntimeError("Shared learner lock import is missing.")

for start, end, replacement, name in sorted(
    changes, reverse=True
):
    lines[start:end] = [replacement]

updated = "".join(lines)

# Validate the complete updated module before writing.
ast.parse(updated)

path.write_text(updated, encoding="utf-8")

print("REMAINING ENDPOINT LOCKS UPDATED")
for name in sorted(functions):
    print("Protected:", name)
print("Python syntax: VERIFIED")
