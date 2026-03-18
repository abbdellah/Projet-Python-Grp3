import importlib
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.database as db


SCHEMA_SQL = """
DROP TABLE IF EXISTS tentative;
DROP TABLE IF EXISTS statut_apprentissage;
DROP TABLE IF EXISTS apprenant;
DROP TABLE IF EXISTS aav;

CREATE TABLE aav (
    id_aav INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    discipline TEXT,
    regles_progression TEXT
);

CREATE TABLE apprenant (
    id_apprenant INTEGER PRIMARY KEY,
    nom_utilisateur TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE statut_apprentissage (
    id INTEGER PRIMARY KEY,
    id_apprenant INTEGER NOT NULL,
    id_aav_cible INTEGER NOT NULL,
    niveau_maitrise REAL DEFAULT 0,
    historique_tentatives_ids TEXT,
    date_debut_apprentissage TEXT,
    date_derniere_session TEXT
);

CREATE TABLE tentative (
    id INTEGER PRIMARY KEY,
    id_exercice_ou_evenement INTEGER NOT NULL,
    id_apprenant INTEGER NOT NULL,
    id_aav_cible INTEGER NOT NULL,
    score_obtenu REAL NOT NULL,
    date_tentative TEXT DEFAULT CURRENT_TIMESTAMP,
    est_valide INTEGER NOT NULL,
    temps_resolution_secondes INTEGER,
    metadata TEXT
);
"""


DATA_SQL = """
INSERT INTO aav (id_aav, nom, discipline, regles_progression)
VALUES (
    1,
    'AAV 1',
    'Math',
    '{"seuil_succes": 0.8, "nombre_succes_consecutifs": 3}'
);

INSERT INTO apprenant (id_apprenant, nom_utilisateur, email)
VALUES (
    2,
    'Bob',
    'bob@example.com'
);

INSERT INTO statut_apprentissage (
    id,
    id_apprenant,
    id_aav_cible,
    niveau_maitrise,
    historique_tentatives_ids,
    date_debut_apprentissage,
    date_derniere_session
)
VALUES (
    1,
    2,
    1,
    0.85,
    '[1, 2, 3]',
    '2026-01-01 10:00:00',
    '2026-01-01 10:10:00'
);

INSERT INTO tentative (
    id,
    id_exercice_ou_evenement,
    id_apprenant,
    id_aav_cible,
    score_obtenu,
    date_tentative,
    est_valide,
    temps_resolution_secondes,
    metadata
)
VALUES
(1, 1001, 2, 1, 0.70, '2026-01-01 10:00:00', 1, 120, NULL),
(2, 1002, 2, 1, 0.80, '2026-01-01 10:05:00', 1, 110, NULL),
(3, 1003, 2, 1, 0.85, '2026-01-01 10:10:00', 1, 100, NULL);
"""


@pytest.fixture()
def client(tmp_path: Path):
    test_db = tmp_path / "test_prof.db"
    db.DATABASE_PATH = test_db

    with sqlite3.connect(test_db) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(DATA_SQL)
        conn.commit()

    import app.routers.attempts as attempts
    importlib.reload(attempts)

    app = FastAPI()
    app.include_router(attempts.router)

    with TestClient(app) as c:
        yield c


def test_process_bob_aav1_reaches_mastery_with_prof_rules(client):
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 1004,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.90,
            "est_valide": True,
            "temps_resolution_secondes": 95,
            "metadata": {"source": "prof_test"},
        },
    )
    assert r.status_code == 201
    attempt_id = r.json()["id"]

    r2 = client.post(f"/attempts/{attempt_id}/process")
    assert r2.status_code == 200

    data = r2.json()
    assert data["tentative_id"] == attempt_id
    assert data["id_apprenant"] == 2
    assert data["id_aav_cible"] == 1
    assert data["ancien_niveau"] == 0.85
    assert data["nouveau_niveau"] == 1.0
    assert data["est_maitrise"] is True