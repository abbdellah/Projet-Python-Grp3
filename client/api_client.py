from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests
from requests import Session


class ApiClientError(Exception):
    """Erreur lisible cote interface pour les appels HTTP."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        """Initialise une erreur applicative exploitable par l'interface.

        Args:
            message: Message court affiche a l'utilisateur.
            status_code: Code HTTP retourne par l'API, quand il existe.
            details: Payload brut ou detail technique conserve pour le debug.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


@dataclass
class PlatonAAVClient:
    """Petit adaptateur HTTP autour de requests."""

    base_url: str = "http://127.0.0.1:8000"
    timeout: float = 5.0
    session: Session = field(default_factory=requests.Session)

    def set_base_url(self, base_url: str) -> None:
        """Met a jour l'URL racine utilisee pour les appels API.

        Args:
            base_url: URL saisie dans l'interface, avec ou sans slash final.
        """
        self.base_url = base_url.strip().rstrip("/")

    def _url(self, path: str) -> str:
        """Construit une URL complete a partir d'un chemin d'endpoint.

        Args:
            path: Chemin relatif de l'API, par exemple `/aavs/`.

        Returns:
            URL absolue prete a etre envoyee a `requests`.
        """
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url.rstrip('/')}{path}"

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Execute une requete HTTP et normalise la reponse.

        Args:
            method: Methode HTTP (`GET`, `POST`, `PATCH`, etc.).
            path: Chemin de l'endpoint appele.
            **kwargs: Parametres transmis directement a `requests`.

        Returns:
            Payload JSON decode, texte brut, ou `None` pour une reponse 204.

        Raises:
            ApiClientError: Si l'API est inaccessible ou retourne une erreur HTTP.
        """
        try:
            response = self.session.request(
                method,
                self._url(path),
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiClientError(
                "Impossible de joindre l'API. Verifiez que le serveur FastAPI est lance.",
                details=str(exc),
            ) from exc

        if response.status_code == 204:
            return None

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.status_code >= 400:
            message = self._extract_error_message(payload)
            raise ApiClientError(message, response.status_code, payload)

        return payload

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Envoie une requete GET.

        Args:
            path: Chemin de l'endpoint.
            params: Parametres de query string optionnels.

        Returns:
            Reponse normalisee par `request`.
        """
        return self.request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Envoie une requete POST.

        Args:
            path: Chemin de l'endpoint.
            json: Corps JSON optionnel.

        Returns:
            Reponse normalisee par `request`.
        """
        return self.request("POST", path, json=json)

    def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Envoie une requete PUT.

        Args:
            path: Chemin de l'endpoint.
            json: Corps JSON optionnel.

        Returns:
            Reponse normalisee par `request`.
        """
        return self.request("PUT", path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Envoie une requete PATCH.

        Args:
            path: Chemin de l'endpoint.
            json: Corps JSON optionnel.

        Returns:
            Reponse normalisee par `request`.
        """
        return self.request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        """Envoie une requete DELETE.

        Args:
            path: Chemin de l'endpoint.

        Returns:
            Reponse normalisee par `request`, souvent `None`.
        """
        return self.request("DELETE", path)

    @staticmethod
    def _extract_error_message(payload: Any) -> str:
        """Extrait le message le plus lisible d'une reponse d'erreur API.

        Args:
            payload: Corps de reponse decode ou texte brut.

        Returns:
            Message destine a etre affiche dans l'interface.
        """
        if isinstance(payload, dict):
            if payload.get("message"):
                return str(payload["message"])
            if payload.get("detail"):
                return str(payload["detail"])
            if payload.get("error"):
                return str(payload["error"])
        return str(payload)
