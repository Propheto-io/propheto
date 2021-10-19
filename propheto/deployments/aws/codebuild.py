import re
import json
from time import sleep
from typing import Optional
from .boto_session import BotoInterface
import logging

logger = logging.getLogger(__name__)


class CodeBuild(BotoInterface):
    """
    Interface for remotely building images for lambdas
    """

    def __init__(self, profile_name: str, region: Optional[str], project_name: Optional[str] = "") -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.codebuild_client = self.boto_client.client("codebuild")
        self.profile_name = profile_name
        self.project_name = project_name

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        return output_dict

    def __repr__(self) -> str:
        if self.project_name != "":
            return f"CodeBuild(profile_name={self.profile_name}, project_name={self.project_name})"
        else:
            return f"CodeBuild(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.project_name != "":
            return f"CodeBuild(profile_name={self.profile_name}, project_name={self.project_name})"
        else:
            return f"CodeBuild(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "codebuild_client"]:
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
        self.codebuild_client = self.boto_client.client("codebuild")

    def create_project(
        self,
        project_name: str,
        project_description: str,
        service_role_arn: str,
        code_location: str,
    ) -> dict:
        # TODO: SUPPORT OTHER SOURCE CODE
        self.project_name = project_name
        response = self.codebuild_client.create_project(
            name=project_name,
            description=project_description,
            source={
                "type": "S3",
                "location": code_location,
                "buildspec": "buildspec.yml",
                "insecureSsl": False,
            },
            artifacts={"type": "NO_ARTIFACTS",},
            cache={"type": "NO_CACHE"},
            environment={
                "type": "LINUX_CONTAINER",
                "image": "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
                "computeType": "BUILD_GENERAL1_MEDIUM",
                "privilegedMode": True,
                "imagePullCredentialsType": "CODEBUILD",
            },
            serviceRole=service_role_arn,
            timeoutInMinutes=60,
            queuedTimeoutInMinutes=60,
            badgeEnabled=False,
            logsConfig={
                "cloudWatchLogs": {
                    "status": "ENABLED",
                    "groupName": "ProphetoAutoCloudbuild",
                    "streamName": "CloudBuildTestLog",
                },
                "s3Logs": {"status": "DISABLED",},
            },
            concurrentBuildLimit=1,
        )
        return response

    def build_image(self, project_name: str) -> dict:
        response = self.codebuild_client.start_build(projectName=project_name)
        print("Building image...")
        build_id = response["build"]["id"]
        wait_counter = 0
        build_status = "IN_PROGRESS"
        while build_status == "IN_PROGRESS" and wait_counter < 30:
            build_status, status_response = self.get_build_status(build_id)
            wait_counter += 1
            print(f"Build in progress... Status: {build_status} - {wait_counter}/30")
            sleep(15)
        if build_status == "SUCCEEDED":
            print(f"Build completed successfully!")
        else:
            raise Exception(f"Build did not complete successfully - {build_status}")
        return response

    def get_build_status(self, build_id: str) -> str:
        """
        buildStatus list:
            FAILED : The build failed.
            FAULT : The build faulted.
            IN_PROGRESS : The build is still in progress.
            STOPPED : The build stopped.
            SUCCEEDED : The build succeeded.
            TIMED_OUT : The build timed out.
        """
        response = self.codebuild_client.batch_get_builds(ids=[build_id])
        try:
            build_status = response["builds"][0]["buildStatus"]
            return build_status, response
        except KeyError:
            print(response)
            raise Exception

    def destroy(self, project_name: str) -> dict:
        """
        Destroy the ECR resource from AWS
        """
        response = self.codebuild_client.delete_project(name=project_name)
        return response

