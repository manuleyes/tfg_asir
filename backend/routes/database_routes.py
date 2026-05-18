"""
Rutas de gestión de base de datos — solo lectura (SELECT)
GET  /api/db/tables            — lista todas las tablas
GET  /api/db/table/{name}      — contenido de una tabla (paginado)
POST /api/db/query             — ejecutar SQL de solo lectura
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import re

from models.database import get_db, engine
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/db", tags=["Database"])

# ── Utilidad de seguridad ──────────────────────────────────────────────────────
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|EXEC|EXECUTE|ATTACH|PRAGMA\s+\w+\s*=)\b",
    re.IGNORECASE,
)

def _assert_readonly(sql: str):
    """Lanza 400 si el SQL contiene escritura."""
    clean = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)  # quitar comentarios
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)
    if _FORBIDDEN.search(clean):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten consultas de lectura (SELECT). "
                   "Operaciones de escritura no están permitidas."
        )


# ── GET /api/db/tables ────────────────────────────────────────────────────────
@router.get("/tables")
def list_tables(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista todas las tablas disponibles con número de filas."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        result = []
        for table in sorted(tables):
            try:
                count_row = db.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()  # nosec B608
                count = count_row if count_row is not None else 0
            except Exception:
                count = -1
            result.append({"name": table, "rows": count})
        return {"tables": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/db/table/{name} ──────────────────────────────────────────────────
@router.get("/table/{name}")
def get_table(
    name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Devuelve las filas de una tabla (paginado)."""
    # Validar nombre de tabla (solo alfanumérico + guión bajo)
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    try:
        inspector = inspect(engine)
        if name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail="Tabla no encontrada")

        cols = [c["name"] for c in inspector.get_columns(name)]
        offset = (page - 1) * page_size

        count = db.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar() or 0  # nosec B608
        rows_raw = db.execute(
            text(f'SELECT * FROM "{name}" LIMIT :lim OFFSET :off'),  # nosec B608
            {"lim": page_size, "off": offset},
        ).fetchall()

        rows = [dict(zip(cols, r)) for r in rows_raw]
        return {
            "table": name,
            "columns": cols,
            "rows": rows,
            "total": count,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-count // page_size)),  # ceiling division
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/db/query ────────────────────────────────────────────────────────
@router.post("/query")
def execute_query(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ejecuta una consulta SQL de solo lectura y devuelve los resultados."""
    sql = (payload.get("sql") or "").strip()
    if not sql:
        raise HTTPException(status_code=400, detail="La consulta SQL está vacía")

    _assert_readonly(sql)

    try:
        result = db.execute(text(sql))
        cols = list(result.keys()) if result.returns_rows else []
        rows = []
        if result.returns_rows:
            for row in result.fetchmany(1000):   # máximo 1000 filas
                rows.append(dict(zip(cols, row)))
        return {"columns": cols, "rows": rows, "count": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en SQL: {str(e)}")
