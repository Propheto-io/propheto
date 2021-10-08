# from propheto.app import Propheto
from typing import Optional
from .iam import IAM
from .s3 import S3
from .cloudformation import CloudFormation
from .aws_lambda import Lambda
from .api_gateway import APIGateway
from .ecr import ECR
from .codebuild import CodeBuild
from typing import Optional


class AWS(IAM, S3, Lambda, APIGateway, CloudFormation, ECR, CodeBuild):
    """
    AWS Interface class
    """

    def __init__(self, profile_name: str, region: Optional[str] = None, * args, **kwargs):
        self.profile_name = profile_name
        self.iam = IAM(profile_name)
        self.s3 = S3(profile_name)
        self.ecr = ECR(profile_name)
        self.aws_lambda = Lambda(profile_name)
        self.api_gateway = APIGateway(profile_name)
        self.cloud_formation = CloudFormation(profile_name)
        self.code_build = CodeBuild(profile_name)
        self.aws_account_id = self.s3.aws_account_id

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
