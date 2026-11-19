"""Provision privileged users and parent links. Run from project root."""
import argparse, sqlite3, secrets, getpass
from app.auth import AuthStore
from app.main import AUTH_DB_PATH

p=argparse.ArgumentParser()
s=p.add_subparsers(dest="action",required=True)
c=s.add_parser("create");c.add_argument("role",choices=["teacher","parent"]);c.add_argument("email");c.add_argument("--name",required=True)
l=s.add_parser("link");l.add_argument("parent_email");l.add_argument("student_email")
a=p.parse_args();store=AuthStore(AUTH_DB_PATH)
if a.action=="create":
    password=getpass.getpass("New password (min 6 characters): ")
    token,user=store.sign_up(a.name,a.email,password,"N/A","N/A","N/A")
    store._sessions.pop(token,None)
    with sqlite3.connect(AUTH_DB_PATH) as db: db.execute("UPDATE users SET role=? WHERE id=?",(a.role,user.id))
    print(f"Created {a.role} account for {a.email}")
else:
    with sqlite3.connect(AUTH_DB_PATH) as db:
        parent=db.execute("SELECT id FROM users WHERE email=? AND role='parent'",(a.parent_email.lower(),)).fetchone()
        child=db.execute("SELECT id FROM users WHERE email=? AND role='student'",(a.student_email.lower(),)).fetchone()
        if not parent or not child: raise SystemExit("Parent or student account not found with correct role")
        db.execute("INSERT OR IGNORE INTO parent_links(parent_id,student_id) VALUES (?,?)",(parent[0],child[0]))
    print("Parent linked to student")
