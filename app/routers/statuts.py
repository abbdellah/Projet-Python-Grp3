from fastapi import APIRouter, Depends, HTTPException # type: ignore
from typing import List, Optional
from app.database import get_db_connection, from_json, to_json
from app.maitrise import calculer_maitrise, message
from app.models import *
import sqlite3 # Cette ligne elle sert juste à sqlite3.Row

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
    res["est_maitrise"] = (res.get("est_maitrise", 0.0) == 1.0)

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
    res["est_valide"] = (res.get("est_valide", 0.0) == 1.0)

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
        results = cursor.fetchall()

    return [sqlite_to_statut(row) for row in results]

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
        result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Statut d'apprentissage d'ID {statut_id} non trouvé")

    return sqlite_to_statut(result)