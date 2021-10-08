import os
import sys
import logging


logger = logging.getLogger(__name__)


class Log:
    """
    Create logs and metrics for ML service/models
    """

    def __init__(self, directory: str, *args, **kwargs) -> None:
        self.directory = directory

    def log_table(self, data) -> None:
        pass

    def log_plot(self, plot) -> None:
        pass

    def log_float(self, data) -> None:
        pass

    def log_string(self, data) -> None:
        pass
