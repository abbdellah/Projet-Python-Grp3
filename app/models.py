# app/models.py

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
from enum import Enum
from datetime import datetime

# ============================================
# ÉNUMÉRATIONS
# ============================================

class TypeEvaluationAAV(str, Enum):
    """Types d'évaluation possibles pour un AAV."""
    HUMAINE = "Humaine"
    CALCUL = "Calcul Automatisé"
    CHUTE = "Compréhension par Chute"
    INVENTION = "Validation par Invention"
    CRITIQUE = "Exercice de Critique"
    EVALUATION_PAIRS = "Évaluation par les Pairs"
    EVALUATION_AGREGEE = "Agrégation (Composite)"

class TypeAAV(str, Enum):
    """Types d'AAV possibles."""
    ATOMIQUE = "Atomique"
    COMPOSITE = "Composite (Chapitre)"

class NiveauDifficulte(str, Enum):
    """Niveaux de difficulté pour les exercices."""
    DEBUTANT = "debutant"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"

# ============================================
# MODÈLES DE BASE (Communs à tous les groupes)
# ============================================

class RegleProgression(BaseModel):
    """
    Règles déterminant comment un apprenant progresse sur un AAV.

    Exemple:
        - seuil_succes: 0.7 (70% pour réussir)
        - nombre_succes_consecutifs: 3 (3 réussites d'affilée = maîtrise)
    """
    seuil_succes: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Score minimum pour considérer une tentative comme réussie"
    )
    maitrise_requise: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Niveau de maîtrise à atteindre pour valider l'AAV"
    )
    nombre_succes_consecutifs: int = Field(
        default=1,
        ge=1,
        description="Nombre de réussites consécutives requises"
    )
    nombre_jugements_pairs_requis: int = Field(
        default=3,
        ge=1,
        description="Pour évaluation par les pairs: jugements nécessaires"
    )
    tolerance_jugement: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Marge de tolérance pour les évaluations par pairs"
    )

class AAVBase(BaseModel):
    """Champs de base pour un AAV (création et mise à jour)."""
    nom: str = Field(..., min_length=3, max_length=200, description="Nom technique de l'AAV")
    libelle_integration: str = Field(
        ...,
        min_length=5,
        description="Forme grammaticale pour insertion dans une phrase"
    )
    discipline: str = Field(..., min_length=2, description="Discipline (ex: Mathématiques)")
    enseignement: str = Field(..., description="Enseignement spécifique (ex: Algèbre)")
    type_aav: TypeAAV
    description_markdown: str = Field(..., min_length=10, description="Description complète")
    prerequis_ids: List[int] = Field(default_factory=list, description="IDs des AAV prérequis")
    prerequis_externes_codes: List[str] = Field(default_factory=list)
    code_prerequis_interdisciplinaire: Optional[str] = None
    type_evaluation: TypeEvaluationAAV

    @field_validator('libelle_integration')
    @classmethod
    def validate_libelle(cls, v: str) -> str:
        """Vérifie que le libellé peut s'intégrer dans une phrase."""
        phrase_test = f"Nous allons travailler {v}"
        if len(phrase_test) > 250:
            raise ValueError("Libellé trop long pour une phrase fluide")
        return v

class AAVCreate(AAVBase):
    """Modèle pour la création d'un AAV (POST)."""
    id_aav: int = Field(..., gt=0, description="Identifiant unique de l'AAV")
    regles_progression: RegleProgression = Field(default_factory=RegleProgression)

class AAVUpdate(BaseModel):
    """Modèle pour la mise à jour partielle (PATCH). Tous les champs sont optionnels."""
    nom: Optional[str] = Field(None, min_length=3, max_length=200)
    libelle_integration: Optional[str] = None
    description_markdown: Optional[str] = None
    prerequis_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class AAV(AAVBase):
    """Modèle complet d'un AAV (réponse API)."""
    id_aav: int
    is_active: bool = True
    version: int = 1
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuration Pydantic V2."""
        from_attributes = True  # Permet de créer depuis un objet SQLAlchemy/dict

# ============================================
# MODÈLES POUR LES RÉPONSES API
# ============================================

class ErrorResponse(BaseModel):
    """Format standard pour les réponses d'erreur."""
    error: str = Field(..., description="Type d'erreur")
    message: str = Field(..., description="Message lisible par l'utilisateur")
    details: Optional[dict] = Field(None, description="Détails techniques supplémentaires")
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginatedResponse(BaseModel):
    """Format standard pour les réponses paginées."""
    items: List[dict]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_previous: bool

class SuccessResponse(BaseModel):
    """Format standard pour les confirmations de succès."""
    success: bool = True
    message: str
    id: Optional[int] = None
    data: Optional[dict] = None


# ============================================
# MODÈLES GROUPE 3 STATUT & TENTATIVES (faut qu'on se référence aux fichiers database.py pour les colonnes des tables et pas au fichier groupe3_statuts_tentatives.md passke y a pas les mêmes choses mais faut écouter database.py)
# ============================================

# ============================================
# MODÈLES POUR LES STATUTS D'APPRENTISSAGES
# ============================================

class StatutApprentissageCreate(BaseModel):
    """Modèle pour la création d'un statut d'apprentissage (POST)."""
    id_apprenant: int = Field(..., gt=0, description="Identifiant de l'apprenant")
    id_aav_cible: int = Field(..., gt=0, description="Identifiant de l'AAV cible")
    niveau_maitrise: float = Field(default=0.0, ge=0.0, le=1.0, description="Niveau de maîtrise actuel")
    historique_tentatives_ids: List[int] = Field(default_factory=list, description="Tableau des IDs des tentatives passées au format JSON")

class StatutApprentissageUpdate(BaseModel):
    """Modèle pour la mise à jour d'un statut d'apprentissage (PUT)."""
    niveau_maitrise: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nouveau niveau de maîtrise")
    historique_tentatives_ids: Optional[List[int]] = Field(None, description="Nouveau tableau des IDs des tentatives passées au format JSON")

class StatutApprentissageMasteryUpdate(BaseModel):
    """Modèle pour la mise à jour du niveau de maîtrise d'un statut d'apprentissage (PUT)."""
    niveau_maitrise: float = Field(..., ge=0.0, le=1.0, description="Nouveau niveau de maîtrise")

class StatutApprentissage(BaseModel):
    """Modèle complet d'un statut d'apprentissage (réponse API)."""
    id: int
    id_apprenant: int
    id_aav_cible: int
    niveau_maitrise: float
    historique_tentatives_ids: List[int] = []
    date_debut_apprentissage: datetime
    date_derniere_session: Optional[datetime] = None
    est_maitrise: bool = False

    class Config:
        """Configuration Pydantic V2."""
        from_attributes = True

# ============================================
# MODÈLES POUR LES TENTATIVES D'ÉVALUATION
# ============================================

class TentativeCreate(BaseModel):
    """Modèle pour la création d'une tentative d'évaluation d'un AAV (POST)."""
    id_exercice_ou_evenement: int = Field(..., gt=0, description="Identifiant de l'exercice ou de l'événement évalué")
    id_apprenant: int = Field(..., gt=0, description="Identifiant de l'apprenant")
    id_aav_cible: int = Field(..., gt=0, description="Identifiant de l'AAV cible")
    score_obtenu: float = Field(..., ge=0.0, le=1.0, description="Score obtenu lors de la tentative")
    est_valide: bool = Field(default=True, description="Indique si la tentative est valide selon les règles de progressions")
    temps_resolution_secondes: Optional[int] = Field(None, ge=0, description="Temps de résolution en secondes")
    metadata: Optional[dict] = Field(None, description="Infos supplémentaires sur la tentative au format JSON")

    @model_validator('score_obtenu')
    @classmethod
    def arrondir_score(cls, x: float) -> float:
        """
        Arrondit le score à deux chiffres après la virgule

        Args:
            values (float): Le score à arrondir

        Returns:
            float: Le score arrondi à deux chiffres après la virgule
        """
        return round(x, 2)

class Tentative(TentativeCreate):
    """Modèle complet d'une tentative d'évaluation d'un AAV (réponse API)."""
    id: int
    id_exercice_ou_evenement: int
    id_apprenant: int
    id_aav_cible: int
    score_obtenu: float
    date_tentative: datetime
    est_valide: bool
    temps_resolution_secondes: Optional[int] = None
    metadata: Optional[dict] = None

    class Config:
        """Configuration Pydantic V2."""
        from_attributes = True

class Process(BaseModel):
    """Modèle pour raitement d'une tentative (POST /attempts/{id}/process)."""
    tentative_id: int = Field(..., gt=0, description="Identifiant de la tentative traiter")
    id_apprenant: int = Field(..., gt=0, description="Identifiant de l'apprenant")
    id_aav_cible: int = Field(..., gt=0, description="Identifiant de l'AAV cible")
    ancien_niveau: float = Field(..., ge=0.0, le=1.0, description="Niveau de maîtrise avant la tentative")
    nouveau_niveau: float = Field(..., ge=0.0, le=1.0, description="Niveau de maîtrise après la tentative")
    est_maitrise: bool = Field(..., description="Indique si l'apprenant a réussi à maîtriser l'AAV après cette tentative")
    message: str = Field(..., description="Message de retour pour l'apprenant") # Est ce que on met ce champ en optionnel ou pas à voir ?