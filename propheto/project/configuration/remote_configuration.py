from typing import Optional
from ..api import API
from .configuration import Configuration


class RemoteConfiguration(API, Configuration):
    """
    Manage configuration with the remote Propheto API.
    """

    def __init__(
        self,
        credentials: dict,
        id: str = "",
        name: str = "",
        version: str = "",
        description: str = "",
    ) -> None:
        API.__init__(self, credentials)
        Configuration.__init__(self, id, name, version, description)

    def get_configuration(
        self, project_name: str = None, project_id: str = None
    ) -> dict:
        """
        Get the remote project config
        """
        if project_name == None and project_id == None:
            raise Exception("Please provide either a 'project_id' or 'project_name'")
        remote_config = self.get_projects(
            project_id=project_id, project_name=project_name
        )
        return remote_config["projects"]

    def write_config(self, configuration: dict) -> dict:
        """
        Call the Propheto API to store the remote config.
        """
        response = self.create_project(configuration)
        return response
