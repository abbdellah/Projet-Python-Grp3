# app/routers/statuts.py
"""
Router pour les Statuts:

Endpoints pour gérer les statuts d'apprentissage (niveau de maîtrise d'un apprenant sur un AAV) ainsi que l'accès à l'historique des tentatives associées
"""

import sqlite3
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException # type: ignore
from ..database import get_db_connection, from_json, to_json
from ..models import StatutApprentissage, StatutApprentissageCreate, StatutApprentissageMasteryUpdate, StatutApprentissageUpdate, Tentative

router = APIRouter(tags=["Statuts"])

def sqlite_to_statut(row: sqlite3.Row) -> StatutApprentissage:
    """
    Convertit une ligne de SQLite en un objet StatutApprentissage

    Args:
        row (sqlite3.Row): Ligne de la base de données à convertir

    Returns:
        StatutApprentissage: L'objet de type StatutApprentissage correspondant à la ligne
    """
    res = dict(row)
    
    tmp = res.get("historique_tentatives_ids")
    res["historique_tentatives_ids"] = from_json(tmp) if tmp else []
    res["est_maitrise"] = (res.get("niveau_maitrise", 0.0) >= 0.9)

    return StatutApprentissage(**res)

def sqlite_to_tentative(row: sqlite3.Row) -> Tentative:
    """
    Convertit une ligne de SQLite en un objet Tentative

    Args:
        row (sqlite3.Row): Ligne de la base de données à convertir

    Returns:
        Tentative: L'objet de type Tentative correspondant à la ligne
    """
    res = dict(row)
    
    tmp = res.get("metadata")
    res["metadata"] = from_json(tmp) if tmp else None
    res["est_valide"] = bool(res.get("est_valide", 0))

    return Tentative(**res)

@router.get("/learning-status", response_model=List[StatutApprentissage])
def get_learning_status(id_apprenant: Optional[int] = None, id_aav: Optional[int] = None):
    """
    Donne les statuts d'apprentissages avec la possibilité de filtrer en fonction de l'ID de l'apprenant et/ou de l'ID de l'AAV.

    Args:
        id_apprenant (Optional[int], optional): L'ID de l'apprenant. Par défaut à None.
        id_aav (Optional[int], optional): L'ID de l'AAV. Par défaut à None.

    Returns:
        StatutApprentissage: La liste des statuts d'apprentissage correspondants aux critères de filtrage
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM statut_apprentissage WHERE 1"
        args = []

        if id_apprenant is not None:
            query += " AND id_apprenant = ?"
            args.append(id_apprenant)

        if id_aav is not None:
            query += " AND id_aav_cible = ?"
            args.append(id_aav)

        cursor.execute(query, args)
        ress = cursor.fetchall()

    return [sqlite_to_statut(row) for row in ress]

@router.get("/learning-status/{statut_id}", response_model=StatutApprentissage)
def get_learning_status_by_id(statut_id: int):
    """
    Récupère un statut d'apprentissage spécifique grâce à son ID.

    Args:
        statut_id (int): L'ID du statut d'apprentissage à récupérer

    Raises:
        HTTPException: Si le statut d'apprentissage n'est pas trouvé (404)

    Returns:
        StatutApprentissage: Le statut d'apprentissage correspondant à l'ID fourni
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")

    return sqlite_to_statut(res)

@router.post("/learning-status", response_model=StatutApprentissage, status_code=201)
def create_learning_status(statut: StatutApprentissageCreate):
    """
    Crée un nouveau statut d'apprentissage dans la base de données.

    Args:
        statut (StatutApprentissage): L'objet de type StatutApprentissage à créer

    Returns:
        StatutApprentissage: Le statut d'apprentissage nouvellement créé avec son ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM statut_apprentissage WHERE id_apprenant = ? AND id_aav_cible = ?",(statut.id_apprenant, statut.id_aav_cible))
        existe = cursor.fetchone()

    if existe:
        raise HTTPException(status_code=400, detail=f"Un statut d'apprentissage pour l'apprenant {statut.id_apprenant} et l'AAV {statut.id_aav_cible} existe déjà")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO statut_apprentissage (id_apprenant, id_aav_cible, niveau_maitrise, historique_tentatives_ids)
            VALUES (?, ?, ?, ?) RETURNING id
            """,
            (
                statut.id_apprenant,
                statut.id_aav_cible,
                statut.niveau_maitrise,
                to_json(statut.historique_tentatives_ids),
            )
        )
        statut_id = cursor.fetchone()["id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=500, detail="Erreur lors de la création/récupération du statut d'apprentissage")

    return sqlite_to_statut(res)

@router.put("/learning-status/{statut_id}", response_model=StatutApprentissage)
def update_learning_status(statut_id: int, statut: StatutApprentissageUpdate):  # Pr cette fonction faut trouver si y a mieux que tout ces if
    """
    Met à jour un statut d'apprentissage déjà existant dans la base de données.

    Args:
        statut_id (int): L'ID du statut d'apprentissage à mettre à jour
        statut (StatutApprentissage): L'objet de type StatutApprentissage contenant les nouvelles données

    Raises:
        HTTPException: Si le statut d'apprentissage n'est pas trouvé (404)

    Returns:
        StatutApprentissage: Le statut d'apprentissage mis à jour
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        champs_fournies = []
        valeurs = []

        if statut.niveau_maitrise is not None:
            champs_fournies.append("niveau_maitrise = ?")
            valeurs.append(statut.niveau_maitrise)
        
        if statut.historique_tentatives_ids is not None:
            champs_fournies.append("historique_tentatives_ids = ?")
            valeurs.append(to_json(statut.historique_tentatives_ids))

        champs_fournies.append("date_derniere_session = ?")
        valeurs.append(datetime.now())

        valeurs.append(statut_id)
        cursor.execute(f"UPDATE statut_apprentissage SET {', '.join(champs_fournies)} WHERE id = ?", valeurs)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")
    
    return sqlite_to_statut(res)

@router.patch("/learning-status/{statut_id}/mastery", response_model=StatutApprentissage)
def update_mastery(statut_id: int, statut: StatutApprentissageMasteryUpdate):
    """
    Met à jour le niveau de maîtrise d'un statut d'apprentissage en fonction d'une nouvelle tentative.

    Args:
        statut_id (int): L'ID du statut d'apprentissage à mettre à jour
        statut (StatutApprentissageMasteryUpdate): L'objet de type StatutApprentissageMasteryUpdate contenant les données du nouveau niveau de maîtrise

    Raises:
        HTTPException: Si le statut d'apprentissage n'est pas trouvé (404)

    Returns:
        StatutApprentissage: Le statut d'apprentissage mis à jour avec le nouveau niveau de maîtrise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE statut_apprentissage SET niveau_maitrise = ?, date_derniere_session = ? WHERE id = ?", (statut.niveau_maitrise, datetime.now(), statut_id))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (statut_id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")
    
    return sqlite_to_statut(res)

@router.get("/learning-status/{id}/attempts", response_model=List[Tentative])
def get_attempts_by_id(id: int):
    """
    Retourne l'historique des tentatives d'un statut d'apprentissage spécifique grâce à son ID.

    Args:
        id (int): L'ID du statut d'apprentissage

    Returns:
        List[Tentative]: La liste des tentatives correspondantes
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (id,))
        statut = cursor.fetchone()

    if not statut:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {id} non trouvé")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM tentative
               WHERE id_apprenant = ? AND id_aav_cible = ?
               ORDER BY date_tentative ASC""",
            (statut["id_apprenant"], statut["id_aav_cible"])
        )
        res = cursor.fetchall()

    return [sqlite_to_tentative(row) for row in res]


@router.get("/learning-status/{id}/attempts/timeline", response_model=List[Tentative])
def get_attempts_timeline_by_id(id: int):
    """
    Retourne la vue chronologique des tentatives d'un statut d'apprentissage spécifique grâce à son ID (vue chronologique des progrès).

    Args:
        id (int): L'ID du statut d'apprentissage

    Returns:
        List[Tentative]: La liste des tentatives correspondantes
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (id,))
        statut = cursor.fetchone()

    if not statut:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {id} non trouvé")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM tentative
               WHERE id_apprenant = ? AND id_aav_cible = ?
               ORDER BY date_tentative DESC""",
            (statut["id_apprenant"], statut["id_aav_cible"])
        )
        res = cursor.fetchall()
    
    return [sqlite_to_tentative(row) for row in res]

@router.post("/learning-status/{id}/reset", response_model=StatutApprentissage)
def reset_learning_status(id: int):
    """
    Réinitialise un statut d'apprentissage à zéro.

    Args:
        id (int): L'ID du statut d'apprentissage à réinitialiser

    Returns:
        StatutApprentissage: Le statut d'apprentissage réinitialisé
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (id,))
        statut = cursor.fetchone()
    
    if not statut:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {id} non trouvé")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE statut_apprentissage
               SET niveau_maitrise = 0.0,
                   historique_tentatives_ids = ?,
                   date_derniere_session = ?
               WHERE id = ?""",
            (to_json([]), datetime.now().isoformat(), id)
        )

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statut_apprentissage WHERE id = ?", (id,))
        res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {id} non trouvé")
    
    return sqlite_to_statut(res)

