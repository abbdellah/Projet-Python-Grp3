# Analyse du framework Tkinter

## Choix retenu

Le client lourd du projet part sur Tkinter avec les widgets `ttk`.

Tkinter est la bibliotheque graphique standard de Python. Elle permet de creer une vraie application desktop sans installer de moteur graphique supplementaire. Dans notre contexte, c'est le choix le plus simple car toute l'equipe peut rester sur Python.

## Pourquoi Tkinter

- Il est disponible avec Python sur la plupart des installations.
- Il ne demande pas d'apprendre JavaScript, HTML/CSS, Java, C# ou un autre langage.
- Il suffit pour les besoins du sujet: listes, formulaires, boutons, onglets, messages d'erreur.
- Il fonctionne bien avec `requests`, donc le client peut consommer l'API FastAPI proprement.
- Il permet de separer le code en vues, services et client HTTP.

## Limites

- Le rendu visuel est plus simple que PySide6 ou PyQt.
- Les interfaces tres modernes demandent plus de travail manuel.
- Tkinter n'est pas ideal pour des graphes tres interactifs complexes. Pour le bonus graphe, on pourra soit utiliser un `Canvas`, soit generer une vue simple des prerequis.

## Alternatives et comparaison rapide

| Framework | Points forts | Points faibles |
| --- | --- | --- |
| Tkinter | Simple, inclus avec Python, rapide a prendre en main | Design plus classique |
| PySide6 / PyQt | Plus moderne, beaucoup de widgets | Installation plus lourde, API plus vaste |
| Kivy | Bon pour interfaces tactiles | Style different, moins adapte a une app de gestion classique |
| Web app | Interface tres flexible | Demande HTML/CSS/JavaScript ou un framework web front |

## Architecture choisie

Le client est separe en trois couches:

- `client/api_client.py`: appelle l'API avec `requests` et transforme les erreurs HTTP en erreurs lisibles.
- `client/services/`: contient les operations metier appelees par l'interface.
- `client/views/`: contient la fenetre Tkinter et les interactions utilisateur.
- `client/demo_data.py`: charge un jeu de donnees de demonstration en passant par l'API.

Les formulaires reutilisent les modeles Pydantic du serveur (`AAVCreate`, `AAVUpdate`, `TentativeCreate`). Cela permet de valider les donnees avant l'appel API et de respecter la consigne du sujet.

Le graphe des relations AAV utilise un `Canvas` Tkinter. Cela reste simple, mais suffisant pour montrer les prerequis et les relations entre AAV atomiques et AAV composites.

## Lancement

Il faut d'abord lancer l'API:

```powershell
py -m uvicorn app.main:app --reload
```

Puis lancer le client Tkinter dans un autre terminal:

```powershell
py -m client.main
```
