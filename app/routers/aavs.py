# app/routers/aavs.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..models import AAV, AAVCreate, AAVUpdate
from ..database import get_db_connection, BaseRepository, to_json

router = APIRouter(
    prefix="/aavs",
    tags=["AAVs"],
    responses={
        404: {"description": "AAV non trouvé"},
        422: {"description": "Données invalides"},
    },
)


JSON_FIELDS = {
    "prerequis_ids",
    "prerequis_externes_codes",
    "aav_enfant_ponderation",
    "ids_exercices",
    "prompts_fabrication_ids",
    "regles_progression",
}


def _dump_for_storage(value):
    """Convertit les valeurs Pydantic en valeurs stockables par SQLite."""
    if hasattr(value, "model_dump"):
        return to_json(value.model_dump())
    if isinstance(value, (list, tuple, dict)):
        return to_json(value)
    return value


def _aav_from_data(data: dict) -> AAV:
    """Construit un modele AAV depuis une ligne SQLite."""
    return AAV(**data)


# Repository spécifique


class AAVRepository(BaseRepository):
    def __init__(self):
        """Initialise le repository specialise pour la table `aav`."""
        super().__init__("aav", "id_aav")

    def get_by_id(self, id_value: int):
        """Recupere un AAV actif par son identifiant."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM aav WHERE id_aav = ? AND is_active = 1",
                (id_value,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create(self, data: dict) -> int:
        """Crée un AAV et retourne son ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Conversion des listes en JSON
            payload = {
                key: _dump_for_storage(value) if key in JSON_FIELDS else value
                for key, value in data.items()
            }

            cursor.execute(
                """
                INSERT INTO aav (
                    id_aav, nom, libelle_integration, discipline, enseignement,
                    type_aav, description_markdown,
                    prerequis_ids, prerequis_externes_codes,
                    code_prerequis_interdisciplinaire, aav_enfant_ponderation,
                    type_evaluation, ids_exercices, prompts_fabrication_ids,
                    regles_progression
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    payload["id_aav"],
                    payload["nom"],
                    payload["libelle_integration"],
                    payload["discipline"],
                    payload["enseignement"],
                    payload["type_aav"],
                    payload["description_markdown"],
                    payload.get("prerequis_ids", "[]"),
                    payload.get("prerequis_externes_codes", "[]"),
                    payload.get("code_prerequis_interdisciplinaire"),
                    payload.get("aav_enfant_ponderation", "[]"),
                    payload["type_evaluation"],
                    payload.get("ids_exercices", "[]"),
                    payload.get("prompts_fabrication_ids", "[]"),
                    payload.get("regles_progression", "{}"),
                ),
            )

            return payload["id_aav"]

    def update(self, id_aav: int, data: dict) -> bool:
        """Met à jour un AAV (partiellement ou complètement)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Construction dynamique de la requête UPDATE
            # Seuls les champs non-null sont mis à jour
            fields = []
            values = []

            for key, value in data.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    # Conversion JSON si nécessaire
                    if key in JSON_FIELDS:
                        value = _dump_for_storage(value)
                    values.append(value)

            if not fields:
                return False

            values.append(id_aav)
            query = f"UPDATE aav SET {', '.join(fields)} WHERE id_aav = ?"

            cursor.execute(query, values)
            return cursor.rowcount > 0


# Instance du repository
repo = AAVRepository()

# ============================================
# ENDPOINTS CRUD
# ============================================


@router.get("/", response_model=List[AAV])
def list_aavs(
    discipline: Optional[str] = Query(None, description="Filtrer par discipline"),
    type_aav: Optional[str] = Query(None, description="Filtrer par type"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Offset pour la pagination"),
):
    """
    Liste tous les AAV avec possibilité de filtrer par discipline ou type.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM aav WHERE is_active = 1"
        params = []

        if discipline:
            query += " AND discipline = ?"
            params.append(discipline)

        if type_aav:
            query += " AND type_aav = ?"
            params.append(type_aav)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [_aav_from_data(dict(row)) for row in rows]


@router.get("/{id_aav}", response_model=AAV)
def get_aav(id_aav: int):
    """
    Récupère un AAV spécifique par son identifiant.
    """
    data = repo.get_by_id(id_aav)
    if not data:
        raise HTTPException(status_code=404, detail="AAV non trouvé")
    return _aav_from_data(data)


@router.post("/", response_model=AAV, status_code=201)
def create_aav(aav: AAVCreate):
    """
    Crée un nouvel AAV. L'ID doit être unique.
    """
    # Vérifier si l'ID existe déjà
    existing = repo.get_by_id(aav.id_aav)
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Un AAV avec l'ID {aav.id_aav} existe déjà"
        )

    try:
        repo.create(aav.model_dump())
        created = repo.get_by_id(aav.id_aav)
        return _aav_from_data(created)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id_aav}", response_model=AAV)
def update_aav_full(id_aav: int, aav: AAVCreate):
    """
    Remplace complètement un AAV (tous les champs).
    """
    existing = repo.get_by_id(id_aav)
    if not existing:
        raise HTTPException(status_code=404, detail="AAV non trouvé")

    # Force l'ID de l'URL
    data = aav.model_dump()
    data["id_aav"] = id_aav

    # Supprimer l'ancien et recréer (ou faire un vrai UPDATE)
    repo.delete(id_aav)
    repo.create(data)

    updated = repo.get_by_id(id_aav)
    return _aav_from_data(updated)


@router.patch("/{id_aav}", response_model=AAV)
def update_aav_partial(id_aav: int, aav: AAVUpdate):
    """
    Met à jour partiellement un AAV (seuls les champs fournis sont modifiés).
    """
    existing = repo.get_by_id(id_aav)
    if not existing:
        raise HTTPException(status_code=404, detail="AAV non trouvé")

    # Ne met à jour que les champs non-null
    update_data = {k: v for k, v in aav.model_dump().items() if v is not None}

    if update_data:
        repo.update(id_aav, update_data)

    updated = repo.get_by_id(id_aav)
    return _aav_from_data(updated)


@router.delete("/{id_aav}", status_code=204)
def delete_aav(id_aav: int):
    """
    Supprime (ou désactive) un AAV.
    Retourne 204 No Content en cas de succès.
    """
    existing = repo.get_by_id(id_aav)
    if not existing:
        raise HTTPException(status_code=404, detail="AAV non trouvé")

    # On va le passer en inactif plutot que de le supprimer
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE aav SET is_active = 0 WHERE id_aav = ?", (id_aav,))

    return None
