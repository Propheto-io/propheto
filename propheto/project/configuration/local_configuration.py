import json
from datetime import date, datetime
from .configuration import Configuration
from typing import Optional


class LocalConfiguration(Configuration):
    """
    Local project configuration.
    """

    def __init__(
        self,
        id: str = "",
        name: str = "",
        version: str = "",
        description: str = "",
        **kwargs,
    ) -> None:
        Configuration.__init__(self, id, name, version, description)

    @staticmethod
    def dict_converter(obj):
        """
        Convert python datetime to iso format 
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"{type(obj)} not datetime")

    def write_config(self, output_file: str = "propheto.config") -> None:
        """
        Write the configuration to a local output
        """
        _config = self.to_dict()
        # remove ignorable attributes
        for attribute in ["_config_path", "_session"]:
            if attribute in _config:
                _config.pop(attribute)
        with open(output_file, "w") as config_file:
            config_file.write(json.dumps(_config, default=self.dict_converter))

    def get_local_configuration(
        self, config_file: Optional[str] = "propheto.config"
    ) -> dict:
        """
        Get the local config.

        Parameters
        ----------
        config_file : str, optional
                The path to the configruation file

        Returns
        -------
        config : dict
        """
        with open(f"{config_file}", "r") as _config_file:
            config = json.load(_config_file)
        Configuration.__init__(self, **config)
        return config

