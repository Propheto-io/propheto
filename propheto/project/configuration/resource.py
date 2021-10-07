from datetime import datetime
from pickle import bytes_types
from time import time
from typing import Optional
import cloudpickle
import base64


class Resource:
    """
    Project resource object
    """

    def __init__(
        self,
        id: str,
        name: str,
        remote_object: object,
        remote_object_args: Optional[dict] = {},
        pickle_object: Optional[bytes] = "",
        created_at: Optional[datetime] = datetime.fromtimestamp(time()),
        updated_at: Optional[datetime] = datetime.fromtimestamp(time()),
        **kwargs,
    ) -> None:
        """
        Parameters
        -----------
        id : str
        name : str
        remote_object : object
        remote_object_args : dict, optional
                Key, value arguments for the remote object.
        
        """
        self.id = id
        self.name = name
        self.remote_object = remote_object
        # TODO: HANDLE PASSING IN ARGUMENTS TO REMOTE OBJECT
        # THIS WILL BE THINGS LIKE PROFILE NAME
        self.remote_object_args = remote_object_args
        self.pickle_object = pickle_object
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        """
        Display the resource as a dictionary object.

        Return 
        ------
        output_dict : dict
                Output dictionary storing the attributes
        """
        output_dict = {}
        output_dict["id"] = self.id
        output_dict["name"] = self.name
        output_dict["created_at"] = self.created_at.isoformat()
        output_dict["updated_at"] = self.updated_at.isoformat()
        output_dict["remote_object"] = str(self.remote_object)
        output_dict["pickle_object"] = self.pickle(self.remote_object)
        return output_dict

    def __repr__(self) -> str:
        return f"Resource(id={self.id}, name={self.name})"

    def __str__(self) -> str:
        return f"id={self.id}, name={self.name}"

    @staticmethod
    def _encode_pickle(bytes_object: bytes) -> str:
        encoded = base64.b64encode(bytes_object)
        return encoded.decode("utf-8")

    @staticmethod
    def _decode_pickle(str_object: str) -> bytes:
        return base64.b64decode(str_object)

    def pickle(self, remote_object: Optional[object] = None) -> str:
        """
        Pickle the remote object
        """
        remote_object = remote_object if remote_object else self.remote_object
        pickle_str = b""
        try:
            pickle_object = cloudpickle.dumps(remote_object)
            pickle_str = self._encode_pickle(pickle_object)
        except:
            print(self.remote_object)
            print(remote_object)
        return pickle_str

    def loads(self, profile_name: Optional[str] = "default", **kwargs):
        """
        Load the remote object resource from the stored pickled object 

        Parameters
        ----------
        profile_name : str, optional
                Default profile name for the boto3 session object.
        """
        bytes_pickle = self._decode_pickle(self.pickle_object)
        self.remote_object = cloudpickle.loads(bytes_pickle)
        self.remote_object.loads(profile_name, **kwargs)

    def destroy(self):
        """
        Destroy the resource.
        """
        self.remote_object.destroy(self.id)
