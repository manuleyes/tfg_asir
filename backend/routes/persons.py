"""
Rutas para Personas Detectadas - GET, SEARCH, etc
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.database import get_db
from models.person import Person
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/personas", tags=["Persons"])


@router.get("")
def get_persons(
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener lista de personas detectadas
    GET /api/personas?limit=100&offset=0
    """
    persons = db.query(Person).order_by(Person.detected_at.desc()).limit(limit).offset(offset).all()
    total = db.query(Person).count()
    
    return {
        "data": persons,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/search")
def search_persons(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Buscar personas por ID
    GET /api/personas/search?q=PERSON_ID
    """
    results = db.query(Person).filter(
        Person.person_id.ilike(f"%{q}%")
    ).limit(50).all()
    
    return results


@router.get("/{person_id}")
def get_person(
    person_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener persona específica
    GET /api/personas/{id}
    """
    person = db.query(Person).filter(Person.person_id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona no encontrada"
        )
    return person


@router.get("/camera/{camera_id}")
def get_persons_by_camera(
    camera_id: int,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener personas detectadas por una cámara específica
    GET /api/personas/camera/{camera_id}
    """
    persons = db.query(Person).filter(
        Person.camera_id == camera_id
    ).order_by(Person.detected_at.desc()).limit(limit).all()
    
    return persons
