# Ask Tutor integration patch

Copy `app/auth.py` and `app/main.py` over their counterparts **after backing up the originals**. Keep the rest of your existing `app/` directory, curriculum data, agents and dependencies. Copy `frontend/*.html` into the existing `frontend/` folder. Put `manage_accounts.py` in the project root.

Start backend: `uvicorn app.main:app --reload --port 8000`.

Student signup remains student-only. Provision privileged accounts locally from project root:

`python manage_accounts.py create teacher teacher@example.com --name "Teacher Name"`

`python manage_accounts.py create parent parent@example.com --name "Parent Name"`

Link parent to a previously registered student:

`python manage_accounts.py link parent@example.com student@example.com`

Use the existing login page for all roles. Teacher and parent pages validate `/auth/me`, and protected API endpoints check role. Existing users automatically migrate to student role. This is still a local prototype: sessions are in-memory and have no expiration; CORS is permissive; additional production hardening is necessary. The full backend cannot be integration-tested without your remaining agent, retriever, OCR and teacher_overview modules. Test with backups and a copy of the database first.
