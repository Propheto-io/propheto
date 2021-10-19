import json
from .boto_session import BotoInterface
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ECR(BotoInterface):
    """
    Create and manage AWS Elastic Container Registry.
    """

    def __init__(
        self, profile_name: str, region: str, ecr_repository_name: str = ""
    ) -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.ecr_client = self.boto_client.client("ecr")
        self.profile_name = profile_name
        self.ecr_repository_name = ecr_repository_name

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary.
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        output_dict["ecr_repository_name"] = self.ecr_repository_name
        return output_dict

    def __repr__(self) -> str:
        if self.ecr_repository_name != "":
            return f"ECR(profile_name={self.profile_name}, ecr_repository_name={self.ecr_repository_name})"
        else:
            return f"ECR(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.ecr_repository_name != "":
            return f"ECR(profile_name={self.profile_name}, ecr_repository_name={self.ecr_repository_name})"
        else:
            return f"ECR(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "ecr_client"]:
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
        self.ecr_client = self.boto_client.client("ecr")

    def create_ecr_repository(self, repository_name: str) -> dict:
        """
        Create the given ECR repository.
        """
        self.ecr_repository_name = repository_name
        response = self.ecr_client.create_repository(
            repositoryName=repository_name,
            imageTagMutability="MUTABLE",
            imageScanningConfiguration={"scanOnPush": True},
            encryptionConfiguration={"encryptionType": "AES256",},
        )
        return response

    def describe_repository(self, respository_name: str) -> None:
        """
        Describe the available repository.
        """
        response = self.ecr_client.describe_repositories(
            repositoryNames=[respository_name]
        )
        return response["repositories"][0]

    def list_images(self, repository_name: str, max_results: Optional[int] = 1) -> dict:
        """
        Get the available images for a given repository.
        """
        response = self.ecr_client.list_images(
            repositoryName=repository_name, maxResults=max_results
        )
        return response["imageIds"]

    def get_ecr_image_uri(self, repository_name: str) -> dict:
        """
        Get the image URI for the specificed repository.
        """
        repository = self.describe_repository(repository_name)
        repository_uri = repository["repositoryUri"]
        # TODO: RETAG IMAGES
        # images = self.list_images(repository_name)
        # image_tag = images["imageTag"]
        image_tag = "latest"
        return f"{repository_uri}:{image_tag}"

    def destroy(self, repository_name: str) -> dict:
        """
        Destroy the ECR resource from AWS.
        """
        repository_name = (
            repository_name if repository_name else self.ecr_repository_name
        )
        response = self.ecr_client.delete_repository(
            repositoryName=repository_name, force=True
        )
        return response
