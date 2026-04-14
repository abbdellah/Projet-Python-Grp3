"""
Tests unitaires — Apprenants et prérequis externes (G2).
"""
import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

LEARNER_VALIDE = {
    "id_apprenant": 1, "nom_utilisateur": "jean.dupont",
    "email": "jean.dupont@test.com", "ontologie_reference_id": None,
    "statuts_actifs_ids": [], "codes_prerequis_externes_valides": []
}


@pytest.fixture()
def client(tmp_path: Path):
    """Base isolée + client HTTP pour chaque test."""
    test_db = str(tmp_path / "test.db")
    os.environ['DATABASE_PATH'] = test_db

    import app.database as db
    import importlib
    importlib.reload(db)
    db.init_database()

    from app.main import app
    with TestClient(app) as c:
        yield c

    os.environ.pop('DATABASE_PATH', None)


def test_creer_apprenant(client):
    r = client.post("/learners/", json=LEARNER_VALIDE)
    assert r.status_code == 201
    assert r.json()["nom_utilisateur"] == "jean.dupont"


def test_creer_apprenant_email_invalide(client):
    data = {**LEARNER_VALIDE, "email": "pas-un-email"}
    r = client.post("/learners/", json=data)
    assert r.status_code == 422


def test_creer_apprenant_doublon(client):
    client.post("/learners/", json=LEARNER_VALIDE)
    r = client.post("/learners/", json=LEARNER_VALIDE)
    assert r.status_code == 400


def test_get_apprenant(client):
    client.post("/learners/", json=LEARNER_VALIDE)
    r = client.get("/learners/1")
    assert r.status_code == 200
    assert r.json()["id_apprenant"] == 1


def test_get_apprenant_introuvable(client):
    assert client.get("/learners/99999").status_code == 404


def test_supprimer_apprenant(client):
    client.post("/learners/", json=LEARNER_VALIDE)
    assert client.delete("/learners/1").status_code == 204
    assert client.get("/learners/1").status_code == 404


def test_ajouter_prerequis_externe(client):
    client.post("/learners/", json=LEARNER_VALIDE)
    r = client.post("/learners/1/external-prerequisites",
                    json={"code_prerequis": "MATH-101", "validated_by": "prof"})
    assert r.status_code == 201
    assert r.json()["code_prerequis"] == "MATH-101"


def test_prerequis_externe_doublon(client):
    client.post("/learners/", json=LEARNER_VALIDE)
    client.post("/learners/1/external-prerequisites",
                json={"code_prerequis": "MATH-101"})
    r = client.post("/learners/1/external-prerequisites",
                    json={"code_prerequis": "MATH-101"})
    assert r.status_code == 400
