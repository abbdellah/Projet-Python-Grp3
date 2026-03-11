import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.database as db


@pytest.fixture()
def client(tmp_path: Path):
    db.DATABASE_PATH = tmp_path / "test.db"

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