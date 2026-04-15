from app.database import init_database
from app.main import app
from fastapi.testclient import TestClient
import pytest
import os
import uuid

os.environ["DATABASE_PATH"] = os.path.join(".test-data", "bootstrap.db")

# Client de test
client = TestClient(app, raise_server_exceptions=False)

# Fixture: exécutée avant chaque test


@pytest.fixture(autouse=True)
def setup_database():
    """Initialise une base de données de test propre."""
    # Utiliser une base de test séparée
    os.makedirs(".test-data", exist_ok=True)
    os.environ["DATABASE_PATH"] = os.path.join(
        ".test-data",
        f"test_{uuid.uuid4().hex}.db",
    )

    # Supprimer l'ancienne base de test
    pass

    # Initialiser la base
    init_database()

    yield  # Le test s'exécute ici

    # Nettoyage après le test
    pass


# ============================================
# TESTS CRUD
# ============================================


def test_create_aav():
    """Test la création d'un AAV."""
    response = client.post(
        "/aavs/",
        json={
            "id_aav": 1,
            "nom": "Test AAV",
            "libelle_integration": "le test d'AAV",
            "discipline": "Test",
            "enseignement": "Unit Testing",
            "type_aav": "Atomique",
            "description_markdown": "Description de test valide",
            "prerequis_ids": [],
            "type_evaluation": "Calcul Automatisé",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nom"] == "Test AAV"
    assert data["id_aav"] == 1


def test_get_aav():
    """Test la récupération d'un AAV existant."""
    # Créer un AAV d'abord
    client.post(
        "/aavs/",
        json={
            "id_aav": 2,
            "nom": "AAV à récupérer",
            "libelle_integration": "la récupération",
            "discipline": "Test",
            "enseignement": "Test",
            "type_aav": "Atomique",
            "description_markdown": "Description de test valide",
            "prerequis_ids": [],
            "type_evaluation": "Humaine",
        },
    )

    # Récupérer
    response = client.get("/aavs/2")
    assert response.status_code == 200
    assert response.json()["nom"] == "AAV à récupérer"


def test_get_aav_not_found():
    """Test la récupération d'un AAV inexistant (404)."""
    response = client.get("/aavs/99999")
    assert response.status_code == 404
    assert "non trouvé" in response.json()["message"]


def test_update_aav_partial():
    """Test la mise à jour partielle (PATCH)."""
    # Créer
    client.post(
        "/aavs/",
        json={
            "id_aav": 3,
            "nom": "Nom original",
            "libelle_integration": "l'original",
            "discipline": "Test",
            "enseignement": "Test",
            "type_aav": "Atomique",
            "description_markdown": "Description originale complete",
            "prerequis_ids": [],
            "type_evaluation": "Humaine",
        },
    )

    # Modifier uniquement le nom
    response = client.patch("/aavs/3", json={"nom": "Nom modifié"})
    assert response.status_code == 200
    assert response.json()["nom"] == "Nom modifié"
    assert response.json()["description_markdown"] == "Description originale complete"


def test_update_aav_partial_editable_fields():
    """Test que le PATCH couvre les champs edites par le client lourd."""
    client.post(
        "/aavs/",
        json={
            "id_aav": 31,
            "nom": "AAV complet",
            "libelle_integration": "l'AAV complet",
            "discipline": "Info",
            "enseignement": "Python",
            "type_aav": "Atomique",
            "description_markdown": "Description originale complete",
            "prerequis_ids": [],
            "type_evaluation": "Humaine",
        },
    )

    response = client.patch(
        "/aavs/31",
        json={
            "discipline": "Mathematiques",
            "enseignement": "Algebre",
            "type_evaluation": "Exercice de Critique",
            "prerequis_ids": [1, 2],
            "prerequis_externes_codes": ["PYTHON_BASE"],
            "code_prerequis_interdisciplinaire": "LOGIQUE_BASE",
            "regles_progression": {
                "seuil_succes": 0.8,
                "maitrise_requise": 1.0,
                "nombre_succes_consecutifs": 2,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["discipline"] == "Mathematiques"
    assert data["enseignement"] == "Algebre"
    assert data["type_evaluation"] == "Exercice de Critique"
    assert data["prerequis_ids"] == [1, 2]
    assert data["prerequis_externes_codes"] == ["PYTHON_BASE"]
    assert data["code_prerequis_interdisciplinaire"] == "LOGIQUE_BASE"
    assert data["regles_progression"]["seuil_succes"] == 0.8
    assert data["regles_progression"]["nombre_succes_consecutifs"] == 2


def test_list_aavs_with_filter():
    """Test le filtrage de la liste."""
    # Créer plusieurs AAV
    for i in range(4, 7):
        client.post(
            "/aavs/",
            json={
                "id_aav": i,
                "nom": f"AAV {i}",
                "libelle_integration": f"l'AAV {i}",
                "discipline": "Math" if i % 2 == 0 else "Physique",
                "enseignement": "Test",
                "type_aav": "Atomique",
                "description_markdown": "Description de test valide",
                "prerequis_ids": [],
                "type_evaluation": "Humaine",
            },
        )

    # Filtrer par discipline
    response = client.get("/aavs/?discipline=Math")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # AAV 4 et 6


def test_delete_aav():
    """Test la suppression (soft delete)."""
    # Créer
    client.post(
        "/aavs/",
        json={
            "id_aav": 10,
            "nom": "AAV à supprimer",
            "libelle_integration": "la suppression",
            "discipline": "Test",
            "enseignement": "Test",
            "type_aav": "Atomique",
            "description_markdown": "Description de test valide",
            "prerequis_ids": [],
            "type_evaluation": "Humaine",
        },
    )

    # Supprimer
    response = client.delete("/aavs/10")
    assert response.status_code == 204

    # Vérifier qu'il n'est plus accessible
    response = client.get("/aavs/10")
    assert response.status_code == 404


# ============================================
# TESTS DE VALIDATION
# ============================================


def test_create_aav_invalid_data():
    """Test la création avec données invalides (422)."""
    response = client.post(
        "/aavs/",
        json={
            "id_aav": 20,
            "nom": "AB",  # Trop court (< 3 caractères)
            "libelle_integration": "le test unitaire",
            "discipline": "Test",
            "enseignement": "Test",
            "type_aav": "TypeInvalide",  # Type non valide
            "description_markdown": "Description de test valide",
            "prerequis_ids": [],
            "type_evaluation": "Humaine",
        },
    )

    assert response.status_code == 422
    assert "validation_error" in response.json()["error"]


def test_debug():
    """Test de diagnostic."""
    import os
    from app.database import get_database_path, get_db_connection

    print("\nChemin DB dans le test:", get_database_path())
    print("Variable ENV:", os.environ.get("DATABASE_PATH"))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        print("Tables:", [row[0] for row in cursor.fetchall()])

    # Tenter une insertion directe
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO aav
            (id_aav, nom, discipline, type_aav, type_evaluation)
            VALUES (999, 'Debug', 'Test', 'Atomique', 'Humaine')
        """
        )

    # Vérifier via l'API
    response = client.get("/aavs/999")
    print("Status GET après insertion directe:", response.status_code)
    print("Réponse:", response.json())
