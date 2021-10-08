from .local_configuration import LocalConfiguration
from .remote_configuration import RemoteConfiguration


class ProjectConfiguration(LocalConfiguration, RemoteConfiguration):
    """
    Project configuration class
    """

    def __init__(
        self,
        credentials: dict,
        id: str,
        name: str,
        version: str,
        description: str,
        *args,
        **kwargs
    ) -> None:
        LocalConfiguration.__init__(
            self,
            id=id,
            name=name,
            version=version,
            description=description,
        )
        self.remote_config = RemoteConfiguration.__init__(
            self,
            credentials=credentials,
            id=id,
            name=name,
            version=version,
            description=description,
        )
