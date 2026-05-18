"""migrate_db.py - Migración de BD y cambio de contraseña admin"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from auth.password_hash import hash_password

settings = get_settings()
db_path = settings.sqlite_path

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Columnas actuales
cur.execute("PRAGMA table_info(users)")
existing_cols = {row[1] for row in cur.fetchall()}
print("Columnas actuales:", existing_cols)

# Columnas a añadir
migrations = [
    ("role",                'TEXT NOT NULL DEFAULT "admin"'),
    ("totp_secret",         "TEXT"),
    ("totp_enabled",        "INTEGER NOT NULL DEFAULT 0"),
    ("email_notifications", "INTEGER NOT NULL DEFAULT 0"),
    ("notify_critical",     "INTEGER NOT NULL DEFAULT 1"),
    ("notify_warning",      "INTEGER NOT NULL DEFAULT 0"),
]

for col, definition in migrations:
    if col not in existing_cols:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        print(f"  Agregada columna: {col}")
    else:
        print(f"  Ya existe: {col}")

conn.commit()

# Cambiar contraseña admin a 'admin'
new_hash = hash_password("admin")
cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, "admin"))
conn.commit()
print(f"  Password admin -> 'admin' (filas: {cur.rowcount})")

conn.close()
print("Migracion completada OK.")
