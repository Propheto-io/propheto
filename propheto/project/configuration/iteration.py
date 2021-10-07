import pickle
from typing import Optional, List
from .resource import Resource
from datetime import datetime, date
from time import time
import copy


class Iteration:
    """
    Project iteration
    """

    def __init__(
        self,
        id: str,
        iteration_name: str,
        version: str,
        resources: dict = {},
        status: str = "inactive",
        created_at: datetime = datetime.fromtimestamp(time()),
        updated_at: datetime = datetime.fromtimestamp(time()),
        **kwargs,
    ) -> None:
        self.id = id
        self.iteration_name = iteration_name
        self.version = version
        self.resources = resources
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"Iteration(id={self.id}, iteration_name={self.iteration_name})"

    def __str__(self) -> str:
        return f"id={self.id}, iteration_name={self.iteration_name}"

    def set_status(self, status) -> None:
        self.status = status

    def add_resource(
        self,
        id: str,
        name: str,
        remote_object: object,
        pickle_object: Optional[bytes] = b"",
        created_at: Optional[datetime] = datetime.fromtimestamp(time()),
        updated_at: Optional[datetime] = datetime.fromtimestamp(time()),
        load: Optional[bool] = False,
        *args,
        **kwargs,
    ) -> object:
        """
        Add resources

        Parameters
        -----------
        id : str 
                primary key for the remote object resource

        Returns
        --------
        resource : object
                Resource object
        """
        resource = Resource(
            id=id,
            name=name,
            remote_object=remote_object,
            pickle_object=pickle_object,
            created_at=created_at,
            updated_at=updated_at,
        )
        # If loading the resource that was previously stored
        # then run the following command
        if load:
            resource.loads(**kwargs)
        self.resources[id] = resource
        return self.resources[id]

    def remove_resource(self, resource_id) -> None:
        self.resources.pop(resource_id)

    def to_dict(self) -> dict:
        """
        Convert the class to a dictionary
        """
        output_dict = {}
        # COPY PARENT ITERATION ATTRIBUTES
        for i_key, i_item in vars(self).items():
            # IF NOT RESOURCES JUST COPY ATTRIBUTE
            if i_key != "resources":
                if isinstance(i_item, (datetime, date)):
                    i_item = i_item.isoformat()
                output_dict[i_key] = copy.deepcopy(i_item)
            else:
                # IF RESOURCES THEN ITERATE OVER OBJECTS
                i_resources = i_item
                _resources_dict = {}
                if i_resources != {}:
                    for r_key, r_item in i_resources.items():
                        _resources_dict[r_key] = copy.deepcopy(r_item.to_dict())
                output_dict["resources"] = _resources_dict
        return output_dict

    def destroy(
        self, excludes: Optional[List[str]] = [], includes: Optional[List[str]] = []
    ) -> str:
        """
        Destroy the AWS resources
        """
        for resource_id, resource in self.resources.items():
            if includes != []:
                if resource_id in includes or resource.name in includes:
                    print(f"Destroying - {resource.name}")
                    resource.destroy()
                    print("Destroyed")
            else:
                if resource_id not in excludes and resource.name not in excludes:
                    print(f"Destroying - {resource.name}")
                    resource.destroy()
                    print("Destroyed")
        return "Resources destroyed"
