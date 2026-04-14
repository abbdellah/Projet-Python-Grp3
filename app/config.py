"""
Configuration de l'application PlatonAAV qui contient tous les
paramètres modifiables : chemin de la base, titre de l'API.
"""

import os
from pathlib import Path


def get_database_path() -> Path:
    """
    Retourne le chemin de la base de données soit en lisant la variable d'environnement DATABASE_PATH si 
    elle est définie, sinon utilise 'platonAAV.db' dans le répertoire courant.
    """
    return Path(os.environ.get("DATABASE_PATH", "platonAAV.db"))


API_TITLE = "PlatonAAV API — G2 et G3"
API_DESCRIPTION = """
API REST pour la gestion des Acquis d'Apprentissage Visés (AAV).

## Modules

* **Learners** — Gestion des apprenants, prérequis externes, progression (G2)
* **Statuts** — Suivi du niveau de maîtrise par apprenant/AAV (G3)
* **Tentatives** — Enregistrement et traitement des tentatives d'évaluation (G3)
"""

API_VERSION = "1.0.0"