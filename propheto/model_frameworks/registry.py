import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Model registry for storing the model objects.
    """

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
