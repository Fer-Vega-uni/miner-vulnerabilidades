import os
from typing import Any, Optional
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

class GitHubClientError(Exception):
    """Excepción personalizada para errores en la API de GitHub."""

    pass


class GitHubClient:

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise GitHubClientError(
                "No se encontró el token de GitHub. "
                "Asegúrate de definir la variable de entorno GITHUB_TOKEN."
            )

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = "https://api.github.com"

    def fetch_organization_repos(
        self, org: str
    ) -> list[dict[str, Any]]:
        """Obtiene la lista completa de repositorios de una organización manejando paginación."""
        repos = []
        page = 1
        per_page = 100  

        while True:
            url = f"{self.base_url}/orgs/{org}/repos"
            params = {"per_page": per_page, "page": page, "type": "all"}

            try:
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=10
                )
            except requests.RequestException as e:
                raise GitHubClientError(
                    f"Error de conexión al consultar la API: {e}"
                )

            if response.status_code == 404:
                raise GitHubClientError(
                    f"La organización '{org}' no fue encontrada en GitHub."
                )
            elif response.status_code == 401:
                raise GitHubClientError(
                    "Token de GitHub inválido o no autorizado."
                )
            elif response.status_code != 200:
                msg = response.json().get(
                    "message", "Error desconocido en la API."
                )
                raise GitHubClientError(
                    f"Error API GitHub ({response.status_code}): {msg}"
                )

            data = response.json()

            if not data:
                break  
            for repo in data:
                repos.append(
                    {
                        "name": repo["name"],
                        "clone_url": repo["clone_url"],
                        "html_url": repo["html_url"],
                        "default_branch": repo.get(
                            "default_branch", "main"
                        ),
                    }
                )

            if len(data) < per_page:
                break

            page += 1

        return repos