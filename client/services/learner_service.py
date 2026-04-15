from __future__ import annotations

from app.models import Learner, LearnerCreate, LearningStatus, LearningStatusSummary
from client.api_client import PlatonAAVClient


class LearnerService:
    """Service de consultation des apprenants et de leur progression."""

    def __init__(self, client: PlatonAAVClient) -> None:
        """Initialise le service avec le client HTTP partage.

        Args:
            client: Client HTTP responsable des appels a l'API.
        """
        self.client = client

    def list_learners(self, limit: int = 1000) -> list[Learner]:
        """Recupere les apprenants actifs.

        Args:
            limit: Nombre maximum d'apprenants retournes par l'API.

        Returns:
            Liste d'apprenants valides par Pydantic.
        """
        data = self.client.get("/learners/", params={"limit": limit, "offset": 0})
        return [Learner.model_validate(item) for item in data]

    def get_learner(self, id_apprenant: int) -> Learner:
        """Recupere un apprenant precis.

        Args:
            id_apprenant: Identifiant de l'apprenant.

        Returns:
            Apprenant valide par Pydantic.
        """
        return Learner.model_validate(self.client.get(f"/learners/{id_apprenant}"))

    def create_learner(self, payload: LearnerCreate) -> Learner:
        """Cree un apprenant via l'API.

        Args:
            payload: Donnees de creation validees par `LearnerCreate`.

        Returns:
            Apprenant cree tel que retourne par l'API.
        """
        data = payload.model_dump(mode="json")
        return Learner.model_validate(self.client.post("/learners/", json=data))

    def get_learning_status(self, id_apprenant: int) -> list[LearningStatus]:
        """Recupere les statuts d'apprentissage d'un apprenant.

        Args:
            id_apprenant: Identifiant de l'apprenant.

        Returns:
            Liste des statuts d'apprentissage valides par Pydantic.
        """
        data = self.client.get(f"/learners/{id_apprenant}/learning-status")
        return [LearningStatus.model_validate(item) for item in data]

    def get_summary(self, id_apprenant: int) -> LearningStatusSummary:
        """Recupere le resume de progression d'un apprenant.

        Args:
            id_apprenant: Identifiant de l'apprenant.

        Returns:
            Resume chiffre de la progression de l'apprenant.
        """
        data = self.client.get(f"/learners/{id_apprenant}/learning-status/summary")
        return LearningStatusSummary.model_validate(data)
