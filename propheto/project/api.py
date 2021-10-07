from botocore import credentials
from requests import session
from time import time
from propheto.utilities import unique_id
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class API:
    """
    Propheto project API. Manage remote project resources.
    """

    REFRESH_THRESHOLD = 300
    API_URL = "https://api.getpropheto.com"

    def __init__(self, credentials: dict, **kwargs) -> None:
        self.access_token_expiration = 0
        self.refresh_token = None
        self.access_token = None
        self._session = session()
        self._authorize(credentials)

    def _authorize(self, credentials: dict) -> None:
        url = f"{self.API_URL}/auth/login"
        response = self._session.post(url, json=credentials)
        response_json = response.json()
        if response.status_code == 200 and "idToken" in response_json:
            token = response_json["idToken"]
            self._session.headers.update({"Authorization": f"Bearer {token}"})
            self.access_token = token
            self.refresh_token = response_json['refreshToken']
            self.access_token_expiration = time() + int(response_json['expiresIn'])            
        else:
            raise Exception(response, response.content)

    def _refresh_access_token(self) -> None:
        if self._should_refresh_access_token():
            url = f"{self.API_URL}/auth/refresh-token"
            credentials = {"refresh_token": self.refresh_token}
            response = self._session.post(url, json=credentials)
            response_json = response.json()
            if response.status_code == 200 and "id_token" in response_json:
                token = response_json["id_token"]
                self._session.headers.update({"Authorization": f"Bearer {token}"})
                self.access_token = token
                self.refresh_token = response_json['refresh_token']
                self.access_token_expiration = time() + int(response_json['expires_in'])
            else:
                raise Exception(response, response.content)

    def _should_refresh_access_token(self):
        # to be safe, refresh before the estimated token expiration to account for latency
        safe_expiration_timestamp = (
            self.access_token_expiration - API.REFRESH_THRESHOLD
        )
        return time() >= safe_expiration_timestamp

    def get_projects(
        self, project_id: Optional[str] = None, project_name: Optional[str] = None
    ) -> dict:
        """
        Get a project or specific project filtered by the project name or project id.

        Parameters
        ----------
        project_id : str, optional
                Unique project id generated when the project was first created. If none then use project name or just return all projects.

        project_name : str, optional
                Unique project name used when the project was first created. If none then use project id or just return all projects.
        
        Returns
        -------
        projects : dict
                Projects that match the criteria

        """
        self._refresh_access_token()
        if project_id:
            url = f"{self.API_URL}/projects/{project_id}"
        elif project_name:
            url = f"{self.API_URL}/projects?project_name={project_name}"
        else:
            url = f"{self.API_URL}/projects"
        projects = self._session.get(url)
        return projects.json()

    def create_project(self, payload: dict) -> dict:
        """
        Create a project in the remote resource.

        Parameters
        ----------
        payload : dict
                The payload to pass to create the project.
        
        Returns
        -------
        response : dict
                API response from the project creation
        """
        self._refresh_access_token()
        url = f"{self.API_URL}/projects"
        response = self._session.post(url, json=payload)
        if response.status_code == 200:
            try:
                response_json = response.json()
                self.project_id = response_json["data"]["id"]
                return response_json
            except KeyError:
                print(response.json())
        else:
            raise Exception(response, response.content)

    def update_project(self, project_id: str, payload: dict) -> dict:
        """
        Update an existing project with new or updated resources.

        Parameters
        ----------
        project_id : str
                Project ID for the propheto project to be updated.

        parameters : dict
                Update parameters to pass to the API.
        
        Returns
        -------
        response : dict
                Message from the project updates
        
        """
        self._refresh_access_token()
        url = f"{self.API_URL}/projects/{project_id}"
        response = self._session.put(url, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            raise Exception(response, response.content)

    def delete_project(self, project_id: str) -> dict:
        """
        Delete the project.

        Parameters
        ----------
        project_id : str
                Project ID to delete
        
        Returns
        -------
        response : dict
                Message from the project updates
        
        """
        self._refresh_access_token()
        url = f"{self.API_URL}/projects/{project_id}"
        response = self._session.delete(url)
        return response.json()

