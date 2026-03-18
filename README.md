# Projet Python Groupe 3 — API de gestion des tentatives et statuts d’apprentissage

## Présentation

Ce projet est une API REST développée avec **FastAPI** dans le cadre du projet **PlatonAAV**. Elle permet de gérer les **tentatives** réalisées par un apprenant sur un AAV (Acquis d’Apprentissage Visé) et de suivre l’évolution de son **statut d’apprentissage**. Le dépôt contient actuellement un dossier `app/`, un dossier `tests/`, un fichier `donnees_test.sql` et un `requirements.txt`. 

L’application expose notamment les routes liées aux tentatives et aux statuts, ainsi qu’une route racine `/` et une route de santé `/health`. Le fichier principal `app/main.py` initialise l’application FastAPI, inclut les routeurs `attempts` et `statuts`, puis configure des gestionnaires d’exceptions globaux. 

## Objectif du projet

L’objectif du Groupe 3 est de proposer une API capable de :

- enregistrer une tentative réalisée par un apprenant ;
- consulter les tentatives existantes ;
- supprimer une tentative ;
- traiter une tentative pour mettre à jour le niveau de maîtrise d’un apprenant sur un AAV ;
- consulter les statuts d’apprentissage associés.

## Technologies utilisées

Le projet repose sur :

- **Python**
- **FastAPI**
- **Uvicorn**
- **Pydantic**
- **Pytest**
- **HTTPX**
- **SQLite**

Les dépendances présentes dans le dépôt sont listées dans `requirements.txt` : `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `pytest` et `httpx`. 

## Structure actuelle du projet

```text
Projet-Python-Grp3/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── maitrise.py
│   ├── models.py
│   └── routers/
│       ├── attempts.py
│       └── statuts.py
├── tests/
│   └── test_db.py
├── donnees_test.sql
├── requirements.txt
└── .gitignore
```

Le dépôt public montre bien la présence des répertoires `app/`, `tests/`, ainsi que des fichiers `donnees_test.sql` et `requirements.txt`. 

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/abbdellah/Projet-Python-Grp3.git
cd Projet-Python-Grp3
```

### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
python -m pip install -r requirements.txt
```

Si nécessaire, tu peux aussi installer manuellement les dépendances minimales :

```bash
python -m pip install fastapi uvicorn pytest httpx
```

## Lancer le projet

Pour démarrer le serveur FastAPI :

```bash
uvicorn app.main:app --reload
```

Une fois le serveur lancé, les points d’accès utiles sont :

- API : `http://127.0.0.1:8000`
- Documentation Swagger : `http://127.0.0.1:8000/docs`
- Vérification de l’état du serveur : `http://127.0.0.1:8000/health`

Le fichier `app/main.py` définit bien la route racine `/` et la route `/health`. 

## Routes principales

### Tentatives

Le routeur `app/routers/attempts.py` contient actuellement les routes suivantes :

- `GET /attempts` : lister les tentatives, avec filtres possibles ;
- `GET /attempts/{id}` : récupérer une tentative par son identifiant ;
- `POST /attempts` : créer une nouvelle tentative ;
- `DELETE /attempts/{id}` : supprimer une tentative ;
- `POST /attempts/{id}/process` : traiter une tentative et recalculer le statut d’apprentissage associé. 

### Statuts

Le projet inclut également un routeur `statuts`, chargé depuis `app/main.py`, pour la gestion des statuts d’apprentissage. 

## Fonctionnement de la phase de test

À l’état actuel du projet, la phase de test repose sur un **fichier unique** :

```text
tests/test_db.py
```

Ce test vérifie le scénario suivant :

- un apprenant nommé **Bob** possède déjà un statut de maîtrise de `0.85` sur l’**AAV 1** ;
- trois tentatives existent déjà pour cet apprenant sur cet AAV ;
- une nouvelle tentative est créée avec un score de `0.90` ;
- l’endpoint `POST /attempts/{id}/process` est ensuite appelé ;
- le résultat attendu est que le niveau de maîtrise atteigne `1.0` et que la maîtrise soit validée. 

Autrement dit, le test valide que le traitement d’une tentative met correctement à jour le statut d’apprentissage lorsqu’un cas favorable est rencontré.

## Lancer les tests

Depuis la racine du projet, exécuter :

```bash
python -m pytest -q
```

Le test actuellement retenu dans le projet est `tests/test_db.py`. D’après son contenu, il construit une base de test SQLite locale, injecte des données cohérentes pour Bob et l’AAV 1, puis vérifie le bon comportement des routes du routeur `attempts`. 

## Données de test

Le dépôt contient également un fichier `donnees_test.sql`, prévu pour fournir des données de test au projet. Ce fichier est bien présent à la racine du dépôt. 

## État actuel du projet

À ce stade, le projet permet :

- de lancer une API FastAPI ;
- de manipuler des tentatives via des routes REST ;
- de traiter une tentative pour mettre à jour un statut d’apprentissage ;
- de vérifier le bon fonctionnement de la logique métier principale au moyen d’un test automatisé avec Pytest.

Le projet est donc dans un état **fonctionnel pour la démonstration du Groupe 3**, avec une API opérationnelle et une phase de test simple, claire et exécutable.

## Auteur

Projet réalisé dans le cadre du module Python — **Groupe 3**.
