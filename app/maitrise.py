# app/maitrise.py

from typing import List

def calculer_maitrise(scores: List[float], seuil_succes: float, nombre_succes_consecutifs: int) -> float:
    """
    Calcule le nouveau niveau de maîtrise d'un apprenant pour un AAV en fonction de ses scores récents.

    Args:
        scores (List[float]): Liste de tous les scores obtenus
        seuil_succes (float): Score minimum pour considérer une tentative comme réussie
        nombre_succes_consecutifs (int): Nombre de réussites consécutives requises pour atteindre la maîtrise

    Returns:
        float: Le nouveau niveau de maîtrise
    """
    if not scores:
        return 0.0  # Ici l'apprenant n'a fait encore aucune tentative dc on return 0.0
    
    derniers_scores = scores[-nombre_succes_consecutifs:]   # On prend les N derniers scores
    
    succes_derniers_scores = [score for score in derniers_scores if score >= seuil_succes]  # On garde que les scores qui sont au-dessus du seuil de succès

    if len(derniers_scores) >= nombre_succes_consecutifs and len(succes_derniers_scores) == nombre_succes_consecutifs:  # Si l'apprenant à bien fait N tentatives et que les N derniers scores sont tous des succès alors l'apprenant a atteint la maîtrise
        return 1.0
    
    # Sinon on calcule le niveau de maîtrise en fonction de TOUT les scores et on retourne un chiffre entre 0 et 0.99 passke là l'apprenant n'a pas fait N succès consécutifs. Est ce qu'on devrit pas calculé en fonction des N derniers scores ?
    moyenne = sum(scores) / len(scores) # Ou du coup sum(derniers_scores) / len(derniers_scores) ?
    return min(round(moyenne, 2), 0.99)

def message(ancien_niveau: float, nouveau_niveau: float, est_maitrise: bool, nombre_succes_consecutifs: int) -> str:
    """
    Génère un message pour l'apprenant

    Args:
        ancien_niveau (float): Niveau avant la tentative
        nouveau_niveau (float): Niveau après la tentative
        est_maitrise (bool): True si nouveau niveau == 1.0 False sionon
        nombre_succes_consecutifs (int): Nombre de réussites consécutives requises pour atteindre la maîtrise

    Returns:
        str: Le message pour l'apprenant
    """
    if est_maitrise:
        return f"Félicitations ! Vous avez atteint la maîtrise de cet AAV avec {nombre_succes_consecutifs} réussites consécutives."
    
    if nouveau_niveau > ancien_niveau:
        return f"Bravo ! Votre niveau de maîtrise a augmenté de {ancien_niveau} à {nouveau_niveau}."
    
    return f"Votre niveau de maîtrise est resté à {nouveau_niveau}."