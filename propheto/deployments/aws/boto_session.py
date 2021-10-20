from typing import Optional
from boto3.session import Session as AWS_Session
import logging

logger = logging.getLogger(__name__)


class BotoInterface:
    """
    Interface for interacting with the BOTO client
    """

    def __init__(
        self, profile_name: Optional[str] = "default", region: Optional[str] = None
    ) -> None:
        self.boto_client = AWS_Session(profile_name=profile_name, region_name=region)
        _caller_identiy = self.boto_client.client("sts").get_caller_identity()
        self.aws_account_id = _caller_identiy["Account"]
        self.aws_user_id = _caller_identiy["UserId"]
        self.profile_name = profile_name
        _region = region if region else self.boto_client.region_name
        self.region = _region if _region else "us-east-1"

    def __repr__(self) -> str:
        return f"BotoInterface(profile_name={self.profile_name})"

    def __str__(self) -> str:
        return f"BotoInterface(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client"]:
            if attribute in state:
                del state[attribute]
        return state

    def loads(
        self,
        profile_name: Optional[str] = "default",
        region: Optional[str] = "us-east-1",
    ):
        """
        Set the boto3 client object attributes. 

        Parameters
        ----------
        profile_name : str, optional
                Default profile name for the boto3 session object.
        region : str, optional
                Region for the AWS services
        """
        super().__init__(profile_name=profile_name, region=region)
        self.boto_client = AWS_Session(profile_name=profile_name, region_name=region)
        self.profile_name = profile_name
        _caller_identiy = self.boto_client.client("sts").get_caller_identity()
        self.aws_account_id = _caller_identiy["Account"]
        self.aws_user_id = _caller_identiy["UserId"]

