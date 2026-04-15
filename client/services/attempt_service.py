from __future__ import annotations

from app.models import Process, Tentative, TentativeCreate
from client.api_client import PlatonAAVClient


class AttemptService:
    """Service de creation et traitement des tentatives."""

    def __init__(self, client: PlatonAAVClient) -> None:
        """Initialise le service avec le client HTTP partage.

        Args:
            client: Client HTTP responsable des appels a l'API.
        """
        self.client = client

    def list_attempts(
        self,
        id_apprenant: int | None = None,
        id_aav_cible: int | None = None,
    ) -> list[Tentative]:
        """Liste les tentatives en appliquant des filtres optionnels.

        Args:
            id_apprenant: Identifiant d'apprenant a filtrer.
            id_aav_cible: Identifiant d'AAV cible a filtrer.

        Returns:
            Liste de tentatives validees par Pydantic.
        """
        params: dict[str, int] = {}
        if id_apprenant is not None:
            params["id_apprenant"] = id_apprenant
        if id_aav_cible is not None:
            params["id_aav_cible"] = id_aav_cible

        data = self.client.get("/attempts", params=params)
        return [Tentative.model_validate(item) for item in data]

    def create_attempt(self, payload: TentativeCreate) -> Tentative:
        """Cree une tentative d'evaluation.

        Args:
            payload: Donnees de tentative validees par `TentativeCreate`.

        Returns:
            Tentative creee par l'API.
        """
        data = payload.model_dump(mode="json", exclude_none=True)
        return Tentative.model_validate(self.client.post("/attempts", json=data))

    def process_attempt(self, tentative_id: int) -> Process:
        """Declenche le recalcul de maitrise pour une tentative.

        Args:
            tentative_id: Identifiant de la tentative a traiter.

        Returns:
            Resultat du traitement contenant ancien et nouveau niveau.
        """
        data = self.client.post(f"/attempts/{tentative_id}/process")
        return Process.model_validate(data)
