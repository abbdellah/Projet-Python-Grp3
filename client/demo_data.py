from __future__ import annotations

from dataclasses import dataclass

from app.models import (
    AAVCreate,
    AAVUpdate,
    LearnerCreate,
    RegleProgression,
    TentativeCreate,
    TypeAAV,
    TypeEvaluationAAV,
)
from client.api_client import ApiClientError
from client.services import AAVService, AttemptService, LearnerService


@dataclass(frozen=True)
class DemoLoadResult:
    """Resume du chargement des donnees de demonstration."""

    aavs: int
    learners_created: int
    attempts_created: int


def load_demo_dataset(
    aav_service: AAVService,
    learner_service: LearnerService,
    attempt_service: AttemptService,
) -> DemoLoadResult:
    """Charge un jeu de donnees coherent en passant uniquement par l'API."""

    aavs = _load_aavs(aav_service)
    learners = _load_learners(learner_service)
    attempts = _load_attempts_if_needed(learner_service, attempt_service)
    return DemoLoadResult(aavs=aavs, learners_created=learners, attempts_created=attempts)


def _load_aavs(aav_service: AAVService) -> int:
    """Cree ou met a jour les AAV utilises pour la demonstration.

    Args:
        aav_service: Service client responsable des appels aux endpoints AAV.

    Returns:
        Nombre d'AAV parcourus dans le jeu de donnees demo.

    Raises:
        ApiClientError: Si l'API retourne une erreur autre qu'un doublon attendu.
    """
    demo_aavs = [
        AAVCreate(
            id_aav=1001,
            nom="Variables Python",
            libelle_integration="les variables Python",
            discipline="Informatique",
            enseignement="Python debutant",
            type_aav=TypeAAV.ATOMIQUE,
            description_markdown="Comprendre, creer et utiliser une variable.",
            type_evaluation=TypeEvaluationAAV.HUMAINE,
            regles_progression=RegleProgression(
                seuil_succes=0.7,
                nombre_succes_consecutifs=1,
            ),
        ),
        AAVCreate(
            id_aav=1002,
            nom="Conditions",
            libelle_integration="les conditions",
            discipline="Informatique",
            enseignement="Python debutant",
            type_aav=TypeAAV.ATOMIQUE,
            description_markdown="Utiliser if, elif et else pour orienter un programme.",
            prerequis_ids=[1001],
            type_evaluation=TypeEvaluationAAV.HUMAINE,
            regles_progression=RegleProgression(
                seuil_succes=0.75,
                nombre_succes_consecutifs=2,
            ),
        ),
        AAVCreate(
            id_aav=1003,
            nom="Boucles",
            libelle_integration="les boucles",
            discipline="Informatique",
            enseignement="Python debutant",
            type_aav=TypeAAV.ATOMIQUE,
            description_markdown="Repeter des traitements avec for et while.",
            prerequis_ids=[1001, 1002],
            type_evaluation=TypeEvaluationAAV.HUMAINE,
            regles_progression=RegleProgression(
                seuil_succes=0.75,
                nombre_succes_consecutifs=2,
            ),
        ),
        AAVCreate(
            id_aav=1004,
            nom="Fonctions",
            libelle_integration="les fonctions",
            discipline="Informatique",
            enseignement="Python debutant",
            type_aav=TypeAAV.ATOMIQUE,
            description_markdown="Definir une fonction, passer des parametres et retourner une valeur.",
            prerequis_ids=[1001, 1002],
            type_evaluation=TypeEvaluationAAV.HUMAINE,
            regles_progression=RegleProgression(
                seuil_succes=0.8,
                nombre_succes_consecutifs=2,
            ),
        ),
        AAVCreate(
            id_aav=1005,
            nom="Parcours Python debutant",
            libelle_integration="le parcours Python debutant",
            discipline="Informatique",
            enseignement="Python debutant",
            type_aav=TypeAAV.COMPOSITE,
            description_markdown="AAV composite regroupant les bases de Python.",
            aav_enfant_ponderation=[
                (1001, 0.25),
                (1002, 0.25),
                (1003, 0.25),
                (1004, 0.25),
            ],
            type_evaluation=TypeEvaluationAAV.HUMAINE,
        ),
    ]

    touched = 0
    for payload in demo_aavs:
        try:
            aav_service.create_aav(payload)
        except ApiClientError as exc:
            if exc.status_code not in (400, 409):
                raise
            aav_service.update_aav(payload.id_aav, _update_from_create(payload))
        touched += 1
    return touched


def _load_learners(learner_service: LearnerService) -> int:
    """Cree les apprenants de demonstration si besoin.

    Args:
        learner_service: Service client responsable des endpoints apprenants.

    Returns:
        Nombre d'apprenants reellement crees.

    Raises:
        ApiClientError: Si l'API retourne une erreur autre qu'un doublon attendu.
    """
    demo_learners = [
        LearnerCreate(
            id_apprenant=2001,
            nom_utilisateur="alice",
            email="alice@example.com",
        ),
        LearnerCreate(
            id_apprenant=2002,
            nom_utilisateur="bob",
            email="bob@example.com",
        ),
    ]

    created = 0
    for payload in demo_learners:
        try:
            learner_service.create_learner(payload)
            created += 1
        except ApiClientError as exc:
            if exc.status_code not in (400, 409):
                raise
    return created


def _load_attempts_if_needed(
    learner_service: LearnerService,
    attempt_service: AttemptService,
) -> int:
    """Ajoute des tentatives demo pour Alice lorsque son historique est vide.

    Args:
        learner_service: Service utilise pour verifier les statuts existants.
        attempt_service: Service utilise pour creer et traiter les tentatives.

    Returns:
        Nombre de tentatives creees et traitees.
    """
    try:
        statuses = learner_service.get_learning_status(2001)
    except ApiClientError:
        statuses = []
    if statuses:
        return 0

    attempts = [
        (3001, 1001, 0.95),
        (3002, 1002, 0.82),
        (3003, 1002, 0.86),
        (3004, 1003, 0.58),
    ]
    created = 0
    for exercise_id, aav_id, score in attempts:
        tentative = attempt_service.create_attempt(
            TentativeCreate(
                id_exercice_ou_evenement=exercise_id,
                id_apprenant=2001,
                id_aav_cible=aav_id,
                score_obtenu=score,
                est_valide=True,
                metadata={"source": "demo"},
            )
        )
        attempt_service.process_attempt(tentative.id)
        created += 1
    return created


def _update_from_create(payload: AAVCreate) -> AAVUpdate:
    """Convertit un payload de creation AAV en payload de mise a jour.

    Args:
        payload: Modele de creation contenant aussi l'identifiant.

    Returns:
        Modele `AAVUpdate` sans l'identifiant, compatible avec PATCH.
    """
    data = payload.model_dump()
    data.pop("id_aav", None)
    return AAVUpdate(**data)
