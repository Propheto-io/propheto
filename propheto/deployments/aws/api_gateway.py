from os import remove
from typing import Optional
from .boto_session import BotoInterface
import logging

logger = logging.getLogger(__name__)


class APIGateway(BotoInterface):
    """
    Manage API gateway resources
    """

    def __init__(
        self,
        profile_name: Optional[str] = "default",
        rest_api_id: Optional[str] = None,
        deployment_id: Optional[str] = None,
        api_name: Optional[str] = None,
        service_api_url: Optional[str] = None,
        region: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.apigateway_client = self.boto_client.client("apigateway")
        self.rest_api_id = rest_api_id
        self.deployment_id = deployment_id
        self.profile_name = profile_name
        self.api_name = api_name
        self.service_api_url = service_api_url
        self.region = region

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        output_dict["deployment_id"] = self.deployment_id
        output_dict["rest_api_id"] = self.rest_api_id
        return output_dict

    def __repr__(self) -> str:
        if self.api_name:
            return f"APIGateway(profile_name={self.profile_name}, api_name={self.api_name})"
        else:
            return f"APIGateway(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.api_name:
            return f"APIGateway(profile_name={self.profile_name}, api_name={self.api_name})"
        else:
            return f"APIGateway(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "apigateway_client"]:
            if attribute in state:
                del state[attribute]
        return state

    def loads(self, profile_name: Optional[str] = "default", region: Optional[str] = "us-east-1"):
        """
        Set the boto3 client object attributes. 

        Parameters
        ----------
        profile_name : str, optional
                Default profile name for the boto3 session object.
        region : str, optional
                Region for the service to be deployed to
        """
        super().__init__(profile_name=profile_name, region=region)
        self.apigateway_client = self.boto_client.client("apigateway")

    def set_attributes(self, response) -> None:
        """
        Set attributes for interacting with API
        """
        self.rest_api_id = response["id"]

    def create_rest_api(self, name, description, version) -> None:
        """
        Create a rest API
        """
        self.api_name = name
        response = self.apigateway_client.create_rest_api(
            name=name,
            description=description,
            version=version,
            apiKeySource="HEADER",
            disableExecuteApiEndpoint=False,
            endpointConfiguration={"types": ["REGIONAL"]},
        )
        self.set_attributes(response)

    def get_resources(self):
        """
        Get a list of the resources for each API deployed
        """
        response = self.apigateway_client.get_resources(restApiId=self.rest_api_id)
        return response

    def put_method(self, resource_id: str):
        """
        Create a method for the given resource with method responses
        """
        self.apigateway_client.put_method(
            restApiId=self.rest_api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
            requestParameters={},
        )
        self.apigateway_client.put_method_response(
            restApiId=self.rest_api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            statusCode="200",
            responseModels={"application/json": "Empty"},
        )

    def put_integration(self, resource_id: str, uri: str):
        """
        Create an integration and integration response for a given resource id
        """
        self.apigateway_client.put_integration(
            restApiId=self.rest_api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            integrationHttpMethod="POST",
            type="AWS_PROXY",
            uri=uri,
            contentHandling="CONVERT_TO_TEXT",
        )
        self.apigateway_client.put_integration_response(
            restApiId=self.rest_api_id,
            resourceId=resource_id,
            httpMethod="ANY",
            statusCode="200",
            responseTemplates={"application/json": ""},
        )
        # NEED TO ADD PERMISSION TO LAMBDA CLIENT FOR API GATEWAY

    def create_resource(self, parent_id: str) -> str:
        """
        Create a new child resource
        """
        response = self.apigateway_client.create_resource(
            restApiId=self.rest_api_id, parentId=parent_id, pathPart="{proxy+}",
        )
        child_resource_id = response["id"]
        return child_resource_id

    def create_deployment(
        self,
        stage_name: Optional[str] = "dev",
        stage_description: Optional[str] = "development stage",
        description: Optional[str] = "model api",
        region: Optional[str] = None,
    ) -> str:
        """
        Create deployment stage
        """
        response = self.apigateway_client.create_deployment(
            restApiId=self.rest_api_id,
            stageName=stage_name,
            stageDescription=stage_description,
            description=description,
        )
        self.deployment_id = response["id"]
        region = region if region else self.region
        api_url = f"https://{self.rest_api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
        self.service_api_url = api_url
        return api_url

    def delete_deployment(
        self, api_id: str, deployment_id: str, stage_name: str = "dev"
    ) -> None:
        """
        Delete deployed stage and API
        """
        self.apigateway_client.delete_stage(restApiId=api_id, stageName=stage_name)
        response = self.apigateway_client.delete_deployment(
            restApiId=api_id, deploymentId=self.deployment_id
        )
        response = self.apigateway_client.delete_rest_api(restApiId=api_id)
        return response

    def create_api(self, name: str, description: str, version: str, uri: str) -> None:
        """
        Create the API
        """
        self.create_rest_api(name, description, version)
        resources = self.get_resources()
        resource_id = resources["items"][0]["id"]
        self.put_method(resource_id=resource_id)
        self.put_integration(resource_id=resource_id, uri=uri)
        child_resource_id = self.create_resource(parent_id=resource_id)
        self.put_method(resource_id=child_resource_id)
        self.put_integration(resource_id=child_resource_id, uri=uri)

    def destroy(
        self, api_id: str, deployment_id: str = "", stage_name: str = "dev", **kwargs
    ) -> dict:
        """
        Destroy the given API gateway.
        """
        # TODO CHANGE DESTROY TO ACCEPT PARAMETERS FOR ALL DETAILS TO DELETE
        api_id = self.rest_api_id
        deployment_id = self.deployment_id
        stage_name = "dev"
        response = self.delete_deployment(api_id, deployment_id, stage_name)
        return response
