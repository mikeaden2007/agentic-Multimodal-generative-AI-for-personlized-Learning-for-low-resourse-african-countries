
from pathlib import Path

path = Path("app/learner_model.py")
source = path.read_text(encoding="utf-8-sig")

old = '''    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
'''

new = '''    def _save(self):
        from app.learner_file_lock import learner_file_lock
        import tempfile

        with learner_file_lock(self.learner_id):
            temporary_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.storage_dir,
                    prefix=f".{self.learner_id}_",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    temporary_path = handle.name
                    json.dump(self._data, handle, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())

                os.replace(temporary_path, self.path)
                temporary_path = None

            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)
'''

if source.count(old) != 1:
    raise SystemExit(
        "STOP: Expected _save method not found exactly once. No changes made."
    )

updated = source.replace(old, new, 1)
compile(updated, str(path), "exec")
path.write_text(updated, encoding="utf-8")

print("LEARNER SAVE METHOD UPDATED SUCCESSFULLY")
print("Atomic file replacement: ENABLED")
print("Per-learner save lock: ENABLED")
