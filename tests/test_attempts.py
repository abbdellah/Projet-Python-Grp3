import importlib
import os
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
    test_db = str(tmp_path / "test.db")
    os.environ['DATABASE_PATH'] = test_db
    importlib.reload(db)

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


def test_maitrise_atteinte_apres_succes_consecutifs(client):
    """
    Cas : Bob a déjà 3 tentatives (0.70, 0.80, 0.85).
    Une 4ème tentative à 0.90 doit déclencher la maîtrise car
    les 3 derniers scores [0.80, 0.85, 0.90] sont tous >= 0.8.
    """
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 1004,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.90,
            "est_valide": True,
            "temps_resolution_secondes": 95,
            "metadata": {"source": "test"},
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


def test_maitrise_non_atteinte_scores_insuffisants(client):
    """
    Bob ajoute une tentative à 0.60 (sous le seuil 0.8).
    La maîtrise ne doit pas être atteinte.
    """
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 1005,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.60,
            "est_valide": True,
        },
    )
    assert r.status_code == 201
    attempt_id = r.json()["id"]

    r2 = client.post(f"/attempts/{attempt_id}/process")
    assert r2.status_code == 200

    data = r2.json()
    assert data["nouveau_niveau"] < 1.0
    assert data["est_maitrise"] is False


def test_process_tentative_introuvable(client):
    """
    Appeler /process sur un id inexistant doit retourner 404.
    """
    r = client.post("/attempts/99999/process")
    assert r.status_code == 404


def test_get_tentative_introuvable(client):
    """
    GET sur une tentative inexistante doit retourner 404.
    """
    r = client.get("/attempts/99999")
    assert r.status_code == 404


def test_creer_tentative(client):
    """
    Créer une tentative doit retourner 201 avec les données correctes.
    """
    r = client.post(
        "/attempts",
        json={
            "id_exercice_ou_evenement": 2001,
            "id_apprenant": 2,
            "id_aav_cible": 1,
            "score_obtenu": 0.75,
            "est_valide": True,
            "temps_resolution_secondes": 60,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["score_obtenu"] == 0.75
    assert data["id_apprenant"] == 2
    assert data["est_valide"] is True
    assert "id" in data


def test_lister_tentatives_par_apprenant(client):
    """
    GET /attempts?id_apprenant=2 doit retourner les 3 tentatives de Bob.
    """
    r = client.get("/attempts?id_apprenant=2")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    assert all(t["id_apprenant"] == 2 for t in data)


def test_supprimer_tentative(client):
    """
    DELETE sur une tentative existante doit retourner 204.
    Un GET suivant doit retourner 404.
    """
    r = client.delete("/attempts/1")
    assert r.status_code == 204

    r2 = client.get("/attempts/1")
    assert r2.status_code == 404


def test_supprimer_tentative_inexistante(client):
    """
    DELETE sur un id inexistant doit retourner 404.
    """
    r = client.delete("/attempts/99999")
    assert r.status_code == 404
