from __future__ import annotations

from app.models import AAV, AAVCreate, AAVUpdate
from client.api_client import PlatonAAVClient


class AAVService:
    """Service dedie aux AAV pour isoler l'interface de l'API."""

    def __init__(self, client: PlatonAAVClient) -> None:
        """Initialise le service avec le client HTTP partage.

        Args:
            client: Client HTTP responsable des appels `requests`.
        """
        self.client = client

    def list_aavs(
        self,
        discipline: str | None = None,
        type_aav: str | None = None,
        limit: int = 1000,
    ) -> list[AAV]:
        """Recupere les AAV actifs, avec filtres optionnels.

        Args:
            discipline: Discipline a filtrer, ou `None` pour tout afficher.
            type_aav: Type d'AAV a filtrer, ou `None` pour tout afficher.
            limit: Nombre maximum d'AAV retournes par l'API.

        Returns:
            Liste d'AAV valides par le modele Pydantic `AAV`.
        """
        params: dict[str, object] = {"limit": limit, "offset": 0}
        if discipline:
            params["discipline"] = discipline
        if type_aav:
            params["type_aav"] = type_aav

        data = self.client.get("/aavs/", params=params)
        return [AAV.model_validate(item) for item in data]

    def get_aav(self, id_aav: int) -> AAV:
        """Recupere un AAV precis par identifiant.

        Args:
            id_aav: Identifiant de l'AAV recherche.

        Returns:
            AAV valide par Pydantic.
        """
        return AAV.model_validate(self.client.get(f"/aavs/{id_aav}"))

    def create_aav(self, payload: AAVCreate) -> AAV:
        """Cree un AAV via l'API.

        Args:
            payload: Donnees de creation deja validees par `AAVCreate`.

        Returns:
            AAV cree tel que retourne par l'API.
        """
        data = payload.model_dump(mode="json")
        return AAV.model_validate(self.client.post("/aavs/", json=data))

    def update_aav(self, id_aav: int, payload: AAVUpdate) -> AAV:
        """Met a jour partiellement un AAV via l'API.

        Args:
            id_aav: Identifiant de l'AAV a modifier.
            payload: Donnees partielles validees par `AAVUpdate`.

        Returns:
            AAV mis a jour tel que retourne par l'API.
        """
        data = payload.model_dump(mode="json", exclude_none=True)
        return AAV.model_validate(self.client.patch(f"/aavs/{id_aav}", json=data))

    def delete_aav(self, id_aav: int) -> None:
        """Desactive un AAV via l'API.

        Args:
            id_aav: Identifiant de l'AAV a supprimer logiquement.
        """
        self.client.delete(f"/aavs/{id_aav}")
