# Installation

## Prerequis

- Python 3.11 ou plus recent.
- `pip`.

Le projet a ete verifie localement avec Python 3.14.

## Installer les dependances

Depuis le dossier `Projet-Python-Fusion`:

```powershell
py -m pip install -r requirements.txt
```

## Lancer l'API

```powershell
py -m uvicorn app.main:app --reload
```

L'API sera disponible sur:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

## Lancer le client lourd Tkinter

L'API doit rester lancee dans un premier terminal. Dans un deuxieme terminal, depuis `Projet-Python-Fusion`:

```powershell
py -m client.main
```

Le client utilise par defaut:

```text
http://127.0.0.1:8000
```

Cette URL peut etre changee directement dans la barre superieure de l'application.

Pour initialiser une base de demonstration, cliquer sur `Charger demo` dans l'interface.

## Base de donnees

Par defaut, SQLite utilise le fichier:

```text
platonAAV.db
```

Pour choisir un autre fichier:

```powershell
$env:DATABASE_PATH="chemin\vers\platonAAV.db"
py -m uvicorn app.main:app --reload
```

La base est initialisee automatiquement au demarrage de l'application.

## Lancer les tests

```powershell
py -m pytest tests -p no:cacheprovider
```

Les tests creent des bases SQLite isolees dans `.test-data`. Ce dossier est un artefact local de test.

## Prochaine etape du rendu

Le sujet `sujetCL.pdf` demande ensuite un client lourd. Le serveur fusionne expose deja les routes necessaires pour:

- afficher et filtrer les AAV;
- creer des AAV;
- associer des prerequis;
- selectionner un apprenant;
- simuler une tentative et recalculer la maitrise.
