import json
import copy
from time import time
from typing import Optional, List
from datetime import datetime, date
from .iteration import Iteration
from propheto.utilities import unique_id


class Configuration:
    """
    Base class for configuration of remote project resources.
    """

    def __init__(
        self,
        id: Optional[str] = "",
        name: Optional[str] = "",
        version: Optional[str] = "",
        description: Optional[str] = "",
        current_iteration_id: Optional[str] = "",
        iterations: Optional[dict] = {},
        status: Optional[str] = "inactive",
        service_api_url: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        self.id = id
        self.name = name
        self.version = version
        self.description = description
        self.current_iteration_id = current_iteration_id
        # TODO: FIGURE OUT ITERATIONS
        self.iterations = {}
        self.status = status
        self.service_api_url = service_api_url
        # Check if passing iteration into initialization
        # if so then load iteration values
        if iterations != {}:
            for id, item in iterations.items():
                if id != "iteration_name": # Hack round intializing the iteration
                    item = json.loads(item) if type(item) == str else item
                    item["id"] = id
                    self.add_iteration(**item)

    def __repr__(self) -> str:
        return f"Configuration(id={self.id}, name={self.name}, version={self.version})"

    def __str__(self) -> str:
        return f"id={self.id}, name={self.name}, version={self.version}"

    def to_dict(self) -> dict:
        """
        Convert the object to dictionary keys

        Returns 
        -------
        output_dict : dict
                Dictionary of the object resources.
        """
        output_dict = {}
        config_dict = vars(self)
        for key, attribute in config_dict.items():
            if key == "_session":
                pass
            elif key != "iterations":
                output_dict[key] = copy.deepcopy(attribute)
            else:
                _iterations_dict = {}
                for i_key, _iteration in attribute.items():
                    _iterations_dict[i_key] = copy.deepcopy(_iteration.to_dict())
                output_dict["iterations"] = _iterations_dict
        return output_dict

    @staticmethod
    def dict_converter(obj):
        """
        Convert python datetime to iso format
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"{type(obj)} not datetime")

    def to_json(self) -> str:
        """
        Convert the class object into a json

        Returns
        -------
        _config_json : str
                String representing the configuration
        """
        _config = self.to_dict().copy()
        # remove ignorable attributes
        for attribute in ["_config_path", "_session"]:
            if attribute in _config:
                del _config[attribute]
        _config_json = json.dumps(_config, default=self.dict_converter)
        return _config_json

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

    def add_iteration(
        self,
        iteration_name: str,
        id: str = "",
        version: str = "",
        resources: dict = {},
        status: str = "inactivate",
        set_current: bool = False,
        *args,
        **kwargs,
    ) -> object:
        """
        iteration_name : str
                Name for the iteration/experiment.
        id : str, optional
                Unique id for the iteration. 
        version : str, optional
                Version for the iteration/API endpoint
        resources : dict, optional
                Resource object 
        status : str, optional
                Status of the iteration
        set_current : bool, optional
                Whether the iteration represents the most recent or current deployment of the model
        """
        iteration = Iteration(
            id=id if id != "" else unique_id(length=8),
            iteration_name=iteration_name,
            version=version if version != "" else self.version,
            resources={},
            status=status,
        )
        self.iterations[iteration.id] = iteration
        # Parse the resource and turn into object
        if resources != {}:
            for id, resource in resources.items():
                resource["id"] = id
                resource["iteration_id"] = iteration.id
                resource["created_at"] = datetime.fromisoformat(resource["created_at"])
                resource["updated_at"] = datetime.fromisoformat(resource["updated_at"])
                self.add_resource(**resource)
        if set_current:
            self.set_current_iteration(iteration_id=iteration.id)
        return iteration

    def set_current_iteration(self, iteration_id: str):
        """
        Set the iteration id

        Parameters
        ----------
        iteration_id : str
                Unique Id for the iterations
        """
        self.current_iteration_id = iteration_id

    def add_resource(
        self,
        remote_object: object,
        iteration_id: str = "",
        id: str = "",
        name: str = "",
        pickle_object: Optional[bytes] = b"",
        created_at: datetime = datetime.fromtimestamp(time()),
        updated_at: datetime = datetime.fromtimestamp(time()),
    ) -> None:
        """
        Add a resource to the iteration

        Parameters
        ----------
        remote_object : object
                Object resource
        iteration_id : str, optional
                Identification string for the resource
        id : str, optional
                Id for the specific resource
        name : str, optional
                Name of the resource
        pickle_object : bytes, optional
                Object 
        created_at : datetime, optional
                Created datetime for the object
        updated_at : datetime, optional
                Updated datetime of the object
        """
        iteration_id = iteration_id if iteration_id != "" else self.current_iteration_id
        resource = self.iterations[iteration_id].add_resource(
            id=id,
            remote_object=remote_object,
            pickle_object=pickle_object,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
        )
        return resource

    def loads(
        self,
        iteration_id: Optional[str] = None,
        profile_name: Optional[str] = "default",
    ) -> None:
        """
        Load pickled resources

        Parameters
        ----------
        iteration_id : str, optional
                The id of the iteration which will be destroyed
        profile_name : str, optional
                The profile name to load the resources
        """
        if self.iterations != {}:
            iteration_id = iteration_id if iteration_id else self.current_iteration_id
            iteration_resources = self.iterations[iteration_id].resources
            for id in list(iteration_resources.keys()):
                self.iterations[iteration_id].resources[id].loads(profile_name=profile_name)

    def destroy(
        self,
        iteration_id: Optional[str] = None,
        excludes: Optional[List[str]] = [],
        includes: Optional[List[str]] = [],
    ) -> None:
        """
        Destroy project resources

        Parameters
        ----------
        iteration_id : str, optional
                Optional to specify the specific iteration to destroy
        excludes : List[str], optional
                Excludes specific resources from destroying. 
        includes : List[str], optional
                Includes specific resources that should be destroyed.
        
        """
        iteration_id = iteration_id if iteration_id else self.current_iteration_id
        self.iterations[iteration_id].destroy(excludes=excludes, includes=includes)
