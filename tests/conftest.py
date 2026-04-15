import importlib
import os
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient

import app.database as db


@pytest.fixture()
def client():
    os.makedirs(".test-data", exist_ok=True)
    test_db = Path(".test-data") / f"test_{uuid.uuid4().hex}.db"
    os.environ["DATABASE_PATH"] = str(test_db)
    db.DATABASE_PATH = test_db

    # IMPORTANT: reload attempts AVANT main
    import app.routers.attempts as attempts
    import app.main as main
    importlib.reload(attempts)
    importlib.reload(main)

    with TestClient(main.app) as c:
        with db.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO apprenant (id_apprenant, nom_utilisateur, email) VALUES (1, 'test_user', 'test@example.com')"
            )
            cur.execute(
                "INSERT INTO aav (id_aav, nom, discipline, type_aav) VALUES (1, 'AAV Test', 'Info', 'Atomique')"
            )
        yield c
