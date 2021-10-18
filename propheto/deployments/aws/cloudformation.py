from typing import Optional
from .boto_session import BotoInterface
from troposphere import (
    Ref as cf_Ref,
    Template as cf_Template,
    Parameter as cf_Parameter,
    Output as cf_Output,
    GetAtt as cf_GetAtt,
    Join as cf_Join,
)
from troposphere import (
    apigateway as cf_apigateway,
    codebuild as cf_codebuild,
    ecr as cf_ecr,
    s3 as cf_s3,
    awslambda as cf_awslambda,
)
from troposphere.iam import Policy, Role
from troposphere.constants import NUMBER as cf_NUMBER
from troposphere.codebuild import (
    Artifacts as cf_Artifcats,
    Environment as cf_Environment,
    Project as cf_Project,
    Source as cf_Source,
)
from troposphere.apigateway import (
    ApiStage as cf_ApiStage,
    Deployment as cf_Deployment,
    EndpointConfiguration,
    Integration as cf_Integration,
    IntegrationResponse as cf_IntegrationResponse,
    Method as cf_Method,
    MethodResponse as cf_MethodResponse,
    Resource as cf_Resource,
    RestApi as cf_RestApi,
    Stage as cf_Stage,
)

from troposphere.awslambda import (
    Code as cf_Code,
    Function as cf_Function,
    Permission as cf_Permission,
    MAXIMUM_MEMORY as cf_MAXIMUM_MEMORY,
    MINIMUM_MEMORY as cf_MINIMUM_MEMORY,
)
from troposphere.iam import Policy as cf_Policy, Role as cf_Role
import logging

logger = logging.getLogger(__name__)


class CloudFormation(BotoInterface):
    """
    AWS CloudFormation Template Class
    """

    def __init__(self, profile_name: str, region: Optional[str], *args, **kwargs) -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.cloudformation_client = self.boto_client.client("cloudformation")
        self.profile_name = profile_name
        self.cloud_template = cf_Template()
        # self.cloud_template.set_description(description)
        self.ACCOUNT_ID = self.aws_account_id
        # TODO: CHANGE DEFAULT REGION
        self.REGION = "us-east-1"
        self.LAMBDA_FUNCTION_NAME = self.LAMBDA_EXECUTION_ROLE_NAME = self.API_NAME = ""

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        output_dict["cloud_template"] = self.cloud_template.to_dict()
        output_dict["ACCOUNT_ID"] = self.ACCOUNT_ID
        output_dict["REGION"] = self.REGION
        output_dict["LAMBDA_FUNCTION_NAME"] = self.LAMBDA_FUNCTION_NAME
        return output_dict

    def __repr__(self) -> str:
        return f"CloudFormation(profile_name={self.profile_name})"

    def __str__(self) -> str:
        return f"CloudFormation(profile_name={self.profile_name})"

    def create_s3_bucket(self) -> None:
        # s3_bucket = s3.Bucket(title='ProphetoTestBucket20210719', )
        # cloud_template.add_resource(s3_bucket)
        pass

    def create_lambda_function(
        self,
        ImageURI: Optional[str] = None,
        CodeBucket: Optional[str] = None,
        CodeKey: Optional[str] = None,
    ) -> None:
        # TODO: FUNCTION AND ROLE NAMES
        self.LAMBDA_FUNCTION_NAME = "ProphetoApiExecuteFunction"
        self.LAMBDA_EXECUTION_ROLE_NAME = "ProphetoLambdaExecutionRole"

        MemorySize = self.cloud_template.add_parameter(
            cf_Parameter(
                "LambdaMemorySize",
                Type=cf_NUMBER,
                Description="Amount of memory to allocate to the Lambda Function",
                Default="128",
                MinValue=cf_MINIMUM_MEMORY,
                MaxValue=cf_MAXIMUM_MEMORY,
            )
        )

        Timeout = self.cloud_template.add_parameter(
            cf_Parameter(
                "LambdaTimeout",
                Type=cf_NUMBER,
                Description="Timeout in seconds for the Lambda function",
                Default="600",
            )
        )

        LambdaExecutionRole = self.cloud_template.add_resource(
            cf_Role(
                self.LAMBDA_EXECUTION_ROLE_NAME,
                Path="/",
                Policies=[
                    cf_Policy(
                        PolicyName="root",
                        PolicyDocument={
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Action": ["logs:*"],
                                    "Resource": "arn:aws:logs:*:*:*",
                                    "Effect": "Allow",
                                },
                                {
                                    "Action": ["lambda:*"],
                                    "Resource": "*",
                                    "Effect": "Allow",
                                },
                            ],
                        },
                    )
                ],
                AssumeRolePolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": ["sts:AssumeRole"],
                            "Effect": "Allow",
                            "Principal": {
                                "Service": [
                                    "lambda.amazonaws.com",
                                    "apigateway.amazonaws.com",
                                ]
                            },
                        }
                    ],
                },
            )
        )
        if ImageURI:
            CODE = cf_Code(ImageUri=ImageURI)
            ApiExecuteFunction = self.cloud_template.add_resource(
                cf_Function(
                    self.LAMBDA_FUNCTION_NAME,
                    Code=CODE,
                    PackageType="Image",
                    Role=cf_GetAtt(self.LAMBDA_EXECUTION_ROLE_NAME, "Arn"),
                    MemorySize=cf_Ref(MemorySize),
                    Timeout=cf_Ref(Timeout),
                )
            )
        else:
            CODE = cf_Code(S3Bucket=CodeBucket, S3Key=CodeKey,)
            ApiExecuteFunction = self.cloud_template.add_resource(
                cf_Function(
                    self.LAMBDA_FUNCTION_NAME,
                    Code=CODE,
                    Handler="main.handler",
                    Role=cf_GetAtt(self.LAMBDA_EXECUTION_ROLE_NAME, "Arn"),
                    Runtime="python3.8",
                    MemorySize=cf_Ref(MemorySize),
                    Timeout=cf_Ref(Timeout),
                )
            )

    def create_api_gateway(self) -> object:
        # TODO: PASS IN API NAME
        self.API_NAME = "ProphetoTestApiGateway20210719v7"
        rest_api = self.cloud_template.add_resource(
            cf_RestApi(
                self.API_NAME,
                Name=self.API_NAME,
                EndpointConfiguration={"Types": ["REGIONAL"]},
            )
        )

        # Create a resource to map the lambda function to
        # Create a Lambda API method for the Lambda resource
        URI = cf_Join(
            "",
            [
                f"arn:aws:apigateway:{self.REGION}:lambda:path/2015-03-31/functions/",
                cf_GetAtt(self.LAMBDA_FUNCTION_NAME, "Arn"),
                "/invocations",
            ],
        )
        ## TODO: UPDATE INTEGRATION RESPONSE FOR JSON
        INTEGRATION = cf_Integration(
            Credentials=cf_GetAtt(self.LAMBDA_EXECUTION_ROLE_NAME, "Arn"),
            Type="AWS_PROXY",
            IntegrationHttpMethod="POST",
            IntegrationResponses=[cf_IntegrationResponse(StatusCode="200")],
            Uri=URI,
        )

        parent_method = self.cloud_template.add_resource(
            cf_Method(
                "ParentLambdaMethod",
                DependsOn=self.LAMBDA_FUNCTION_NAME,
                RestApiId=cf_Ref(rest_api),
                AuthorizationType="NONE",
                ResourceId=cf_GetAtt(rest_api, "RootResourceId"),
                HttpMethod="ANY",
                Integration=INTEGRATION,
                MethodResponses=[cf_MethodResponse("CatResponse", StatusCode="200")],
            )
        )

        # Create a resource to map the lambda function to
        child_proxy_resource = self.cloud_template.add_resource(
            cf_Resource(
                "MethodResource",
                DependsOn="ParentLambdaMethod",
                RestApiId=cf_Ref(rest_api),
                PathPart="{proxy+}",
                ParentId=cf_GetAtt(rest_api, "RootResourceId"),
            )
        )

        # Create a Lambda API method for the Lambda resource
        child_method = self.cloud_template.add_resource(
            cf_Method(
                "ChildLambdaMethod",
                DependsOn="MethodResource",
                RestApiId=cf_Ref(rest_api),
                AuthorizationType="NONE",
                ResourceId=cf_Ref(child_proxy_resource),
                HttpMethod="ANY",
                Integration=INTEGRATION,
                MethodResponses=[cf_MethodResponse("CatResponse", StatusCode="200")],
            )
        )
        return rest_api

    def grant_lambda_permissions(self, rest_api: str) -> None:
        parent_permission = self.cloud_template.add_resource(
            cf_Permission(
                "ParentMethodPermission",
                FunctionName=cf_Ref(self.LAMBDA_FUNCTION_NAME),
                Principal="apigateway.amazonaws.com",
                Action="lambda:InvokeFunction",
                SourceArn=cf_Join(
                    "",
                    [
                        f"arn:aws:execute-api:{self.REGION}:{self.ACCOUNT_ID}:",
                        cf_Ref(rest_api),
                        "/*/*/",
                    ],
                ),
            )
        )
        child_permission = self.cloud_template.add_resource(
            cf_Permission(
                "ChildMethodPermission",
                FunctionName=cf_Ref(self.LAMBDA_FUNCTION_NAME),
                Principal="apigateway.amazonaws.com",
                Action="lambda:InvokeFunction",
                SourceArn=cf_Join(
                    "",
                    [
                        f"arn:aws:execute-api:{self.REGION}:{self.ACCOUNT_ID}:",
                        cf_Ref(rest_api),
                        "/*/*/*",
                    ],
                ),
            )
        )

    def create_deployment(self, rest_api: object) -> None:
        # # Create a deployment
        stage_name = "v1"

        deployment = self.cloud_template.add_resource(
            cf_Deployment(
                "%sDeployment" % stage_name,
                DependsOn="ChildLambdaMethod",
                RestApiId=cf_Ref(rest_api),
            )
        )

        stage = self.cloud_template.add_resource(
            cf_Stage(
                "%sStage" % stage_name,
                StageName=stage_name,
                RestApiId=cf_Ref(rest_api),
                DeploymentId=cf_Ref(deployment),
            )
        )

    def create_ecr(self) -> None:
        # ecr_repo = ecr.Repository(title='ProphetoTestECR20210719')
        # cloud_template.add_resource(ecr_repo)
        pass

    def create_codebuild(self) -> None:
        # artifacts = Artifacts(Type="NO_ARTIFACTS")
        # environment = Environment(
        #     ComputeType="BUILD_GENERAL1_SMALL",
        #     Image="aws/codebuild/amazonlinux2-x86_64-standard:3.0",
        #     Type="LINUX_CONTAINER",
        #     EnvironmentVariables=[{"Name": "APP_NAME", "Value": "demo"}],
        # )

        # source = Source(
        #     # Location="codebuild-demo-test/0123ab9a371ebf0187b0fe5614fbb72c",
        #     Location="codebuildsample-us-east-{accountid}-input-bucket/app.zip",
        #     Type="S3",
        # )

        # project = Project(
        #     "ProphetoDemoProject",
        #     Artifacts=artifacts,
        #     Environment=environment,
        #     Name="DemoProject",
        #     ServiceRole="arn:aws:iam::{accountid}:role/service-role/codebuild-test-project-service-role",
        #     Source=source,
        # )
        # cloud_template.add_resource(project)
        pass

    def generate_template(self, image_uri: str) -> str:
        self.create_s3_bucket()
        self.create_ecr()
        self.create_codebuild()
        self.create_lambda_function(ImageURI=image_uri)
        rest_api = self.create_api_gateway()
        self.grant_lambda_permissions(rest_api)
        self.create_deployment(rest_api)
        template_body = self.cloud_template.to_json()
        response = self.cloudformation_client.validate_template(
            TemplateBody=template_body
        )
        return self.cloud_template.to_json()
