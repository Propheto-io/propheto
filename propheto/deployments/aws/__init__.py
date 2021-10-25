# from propheto.app import Propheto
from typing import Optional
from .iam import IAM
from .s3 import S3
from .cloudformation import CloudFormation
from .aws_lambda import Lambda
from .api_gateway import APIGateway
from .ecr import ECR
from .codebuild import CodeBuild
from .cloudwatch import CloudWatch
from typing import Optional


class AWS(IAM, S3, Lambda, APIGateway, CloudFormation, ECR, CodeBuild, CloudWatch):
    """
    AWS Interface class
    """

    def __init__(
        self,
        profile_name: Optional[str] = "default",
        region: Optional[str] = None,
        *args,
        **kwargs
    ):
        self.profile_name = profile_name
        self.iam = IAM(profile_name)
        # If no region specified try to use the default region for the profile
        region = region if region else self.iam.boto_client.region_name
        # If the AWS profiles are not set up with a region then parse a default
        region = region if region else "us-east-1"
        self.region = region
        self.aws_account_id = self.iam.aws_account_id
        self.s3 = S3(profile_name=profile_name, region=region)
        self.ecr = ECR(profile_name, region=region)
        self.aws_lambda = Lambda(profile_name, region=region)
        self.api_gateway = APIGateway(profile_name, region=region)
        self.cloud_formation = CloudFormation(profile_name, region=region)
        self.code_build = CodeBuild(profile_name, region=region)
        self.cloudwatch = CloudWatch(profile_name, region=region)

    def generate_cloudformation(self, description: str) -> None:
        self.cloud_template.set_description(description)
        cf_template = self.generate_template()
        with open("cloudformation_template.json", "w") as cf_file:
            cf_file.write(cf_template)
        print("Created cloudformation template: cloudformation_template.json")

    def deploy_cloudformation(self, name: str, template_file: str = None) -> None:
        if template_file:
            with open(template_file, "r") as file:
                cf_template = file.read()
        else:
            cf_template = self.generate_template()
        self.cloudformation_client.create_stack(
            StackName=name, TemplateBody=cf_template, Capabilities=["CAPABILITY_IAM"]
        )
