
from pathlib import Path
import ast

path = Path("app/main.py")
source = path.read_text(encoding="utf-8")

marker = "# ---------- AskTutor frontend page routes ----------"

if marker in source:
    raise RuntimeError("Frontend routes already added.")

routes = '''

# ---------- AskTutor frontend page routes ----------

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/login.html", include_in_schema=False)
def frontend_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/signup.html", include_in_schema=False)
def frontend_signup():
    return FileResponse(os.path.join(FRONTEND_DIR, "signup.html"))


@app.get("/dashboard.html", include_in_schema=False)
def frontend_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))


@app.get("/teacher.html", include_in_schema=False)
def frontend_teacher():
    return FileResponse(os.path.join(FRONTEND_DIR, "teacher.html"))


@app.get("/parent.html", include_in_schema=False)
def frontend_parent():
    return FileResponse(os.path.join(FRONTEND_DIR, "parent.html"))


@app.get("/admin.html", include_in_schema=False)
def frontend_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

'''

updated = source.rstrip() + "\n" + routes

ast.parse(updated)
path.write_text(updated, encoding="utf-8")

print("FRONTEND ROUTES ADDED")
print("Existing HTML files unchanged")
print("Administrator page route registered")
print("Python syntax verified")
