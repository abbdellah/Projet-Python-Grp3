import importlib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.database as db


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS aav (
    id_aav INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    libelle_integration TEXT,
    discipline TEXT,
    enseignement TEXT,
    type_aav TEXT,
    description_markdown TEXT,
    prerequis_ids TEXT,
    prerequis_externes_codes TEXT,
    code_prerequis_interdisciplinaire TEXT,
    aav_enfant_ponderation TEXT,
    type_evaluation TEXT,
    ids_exercices TEXT,
    prompts_fabrication_ids TEXT,
    regles_progression TEXT,
    is_active INTEGER,
    version INTEGER
);

CREATE TABLE IF NOT EXISTS ontology_reference (
    id_reference INTEGER PRIMARY KEY,
    discipline TEXT,
    aavs_ids_actifs TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS apprenant (
    id_apprenant INTEGER PRIMARY KEY,
    nom_utilisateur TEXT NOT NULL,
    email TEXT NOT NULL,
    ontologie_reference_id INTEGER,
    statuts_actifs_ids TEXT,
    codes_prerequis_externes_valides TEXT,
    date_inscription TEXT,
    derniere_connexion TEXT,
    is_active INTEGER
);

CREATE TABLE IF NOT EXISTS statut_apprentissage (
    id INTEGER PRIMARY KEY,
    id_apprenant INTEGER NOT NULL,
    id_aav_cible INTEGER NOT NULL,
    niveau_maitrise REAL DEFAULT 0,
    historique_tentatives_ids TEXT,
    date_debut_apprentissage TEXT,
    date_derniere_session TEXT,
    FOREIGN KEY (id_apprenant) REFERENCES apprenant(id_apprenant),
    FOREIGN KEY (id_aav_cible) REFERENCES aav(id_aav)
);

CREATE TABLE IF NOT EXISTS tentative (
    id INTEGER PRIMARY KEY,
    id_exercice_ou_evenement INTEGER NOT NULL,
    id_apprenant INTEGER NOT NULL,
    id_aav_cible INTEGER NOT NULL,
    score_obtenu REAL NOT NULL,
    date_tentative TEXT DEFAULT CURRENT_TIMESTAMP,
    est_valide INTEGER NOT NULL,
    temps_resolution_secondes INTEGER,
    metadata TEXT,
    FOREIGN KEY (id_apprenant) REFERENCES apprenant(id_apprenant),
    FOREIGN KEY (id_aav_cible) REFERENCES aav(id_aav)
);
"""


def load_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


@pytest.fixture()
def client(tmp_path: Path):
    test_db = tmp_path / "test.db"
    db.DATABASE_PATH = test_db

    with sqlite3.connect(test_db) as conn:
        conn.executescript(SCHEMA_SQL)
        load_sql_file(conn, Path("donnees_test.sql"))

    import app.routers.attempts as attempts
    import app.main as main

    importlib.reload(attempts)
    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c