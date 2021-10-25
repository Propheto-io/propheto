from typing import Tuple, Optional
from time import sleep
from .boto_session import BotoInterface
from ...utilities import human_size, unique_id
import logging

logger = logging.getLogger(__name__)


class Lambda(BotoInterface):
    """
    Create and manage AWS serverless lambda function from 
    either a zipped S3 python environment file or a ECR Image URI
    """

    def __init__(
        self,
        profile_name: Optional[str] = "default",
        function_name: Optional[str] = "",
        region: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.lambda_client = self.boto_client.client("lambda")
        self.function_name = function_name
        self.profile_name = profile_name

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        return output_dict

    def __repr__(self) -> str:
        if self.function_name != "":
            return f"Lambda(profile_name={self.profile_name}, function_name={self.function_name})"
        else:
            return f"Lambda(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.function_name != "":
            return f"Lambda(profile_name={self.profile_name}, function_name={self.function_name})"
        else:
            return f"Lambda(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "lambda_client"]:
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
                Region for the service to be deployed to
        """
        super().__init__(profile_name=profile_name, region=region)
        self.lambda_client = self.boto_client.client("lambda")

    def get_function_state(self, function_name: str) -> str:
        function_response = self.lambda_client.get_function(FunctionName=function_name)
        state = function_response["Configuration"]["State"]
        return state

    def create_lambda_function(
        self,
        function_name: str,
        role_arn: str,
        s3_bucket_name: str = None,
        s3_bucket_zipfile: str = None,
        image_uri: str = None,
    ) -> Tuple[str]:
        self.function_name = function_name
        if image_uri:
            # "512258118601.dkr.ecr.us-east-1.amazonaws.com/lambda-docker-propheto:latest"
            create_response = self.lambda_client.create_function(
                FunctionName=function_name,
                Description="Propheto automated deploy lambda function",
                Role=role_arn,
                PackageType="Image",
                Code={"ImageUri": image_uri},
                Timeout=360,
                MemorySize=512,
                Publish=True,
            )
        else:
            # TODO: HANDLE OTHER PYTHON VERSIONS
            handler_name = "main.handler"
            create_response = self.lambda_client.create_function(
                FunctionName=function_name,
                Description="Propheto automated deploy lambda function",
                Runtime="python3.8",
                Role=role_arn,
                Handler=handler_name,
                Code={"S3Bucket": s3_bucket_name, "S3Key": s3_bucket_zipfile},
                Timeout=360,
                MemorySize=512,
                Publish=True,
            )
        sleep(5)
        function_cntr = 0
        function_state = self.get_function_state(function_name)
        while function_state == "Pending" and function_cntr < 15:
            function_cntr += 1
            function_state = self.get_function_state(function_name)
            print(f"Function status {function_state}")
            sleep(5)
        function_arn = create_response["FunctionArn"]
        return function_name, function_arn

    def grant_lambda_permission(
        self, rest_api_id: str, function_name: str
    ) -> Tuple[dict]:
        ACCOUNT_ID = self.aws_account_id
        # TODO: FIGURE OUT HOW TO GET REGION
        REGION = self.region
        # Generate a random statement ID for the permission
        statement_id = "Propheto-{0}".format(unique_id())
        source_arn = f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{rest_api_id}/*/*/"
        response_parent = self.lambda_client.add_permission(
            FunctionName=function_name,
            Action="lambda:InvokeFunction",
            SourceArn=source_arn,
            Principal="apigateway.amazonaws.com",
            StatementId=statement_id,
        )
        # NEED TO DO THIS FOR DOCS TO WORK
        statement_id_child = "Propheto-{0}".format(unique_id())
        source_arn_child = (
            f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{rest_api_id}/*/*/*"
        )
        response_child = self.lambda_client.add_permission(
            FunctionName=function_name,
            Action="lambda:InvokeFunction",
            SourceArn=source_arn_child,
            Principal="apigateway.amazonaws.com",
            StatementId=statement_id_child,
        )
        return response_parent, response_child

    def update_lambda_function(self, function_name: str, image_uri: str) -> str:
        """
        Update the lambda function code with a new image
        """
        response = self.lambda_client.update_function_code(
            FunctionName=function_name, ImageUri=image_uri
        )
        return response

    def get_lambda_arn(self, function_name: Optional[str] = "") -> str:
        function_name = function_name if function_name != "" else self.function_name
        response = self.lambda_client.get_function(FunctionName=function_name)
        return response["Configuration"]["FunctionArn"]

    def destroy(self, function_name: str) -> dict:
        response = self.lambda_client.delete_function(FunctionName=function_name)
        return response

