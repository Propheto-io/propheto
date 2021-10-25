import json
from typing import Optional
from .boto_session import BotoInterface
import logging

logger = logging.getLogger(__name__)


ASSUME_POLICY = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "apigateway.amazonaws.com",
          "lambda.amazonaws.com",
          "events.amazonaws.com",
          "s3.amazonaws.com",
          "codebuild.amazonaws.com",
          "events.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}"""


ATTACH_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": "arn:aws:s3:::*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:*"
            ],
            "Resource": "arn:aws:sns:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sqs:*"
            ],
            "Resource": "arn:aws:sqs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:*"
            ],
            "Resource": "arn:aws:dynamodb:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "imagebuilder:GetComponent",
                "imagebuilder:GetContainerRecipe",
                "ecr:GetAuthorizationToken",
                "ecr:BatchGetImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:PutImage"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "*",
            "Condition": {
                "ForAnyValue:StringEquals": {
                    "kms:EncryptionContextKeys": "aws:imagebuilder:arn",
                    "aws:CalledVia": [
                        "imagebuilder.amazonaws.com"
                    ]
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::ec2imagebuilder*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:CreateLogGroup",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:log-group:/aws/imagebuilder/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "events:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codebuild:*"
            ],
            "Resource": "*"
        }
    ]
}"""


class IAM(BotoInterface):
    """
    Manage IAM Roles
    """

    assume_policy_str = ASSUME_POLICY
    attach_policy_str = ATTACH_POLICY
    role_name = "Propheto"

    def __init__(self, profile_name: str, *args, **kwargs) -> None:
        super().__init__(profile_name=profile_name)
        self.iam = self.boto_client.client("iam")
        self.profile_name = profile_name
        self.attach_policy_obj = json.loads(self.attach_policy_str)
        self.assume_policy_obj = json.loads(self.assume_policy_str)

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        return output_dict

    def __repr__(self) -> str:
        return f"IAM(profile_name={self.profile_name})"

    def __str__(self) -> str:
        return f"profile_name={self.profile_name}"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "iam"]:
            if attribute in state:
                del state[attribute]
        return state

    def loads(self, profile_name: Optional[str] = "default"):
        """
        Set the boto3 client object attributes. 

        Parameters
        ----------
        profile_name : str, optional
                Default profile name for the boto3 session object.
        """
        super().__init__(profile_name=profile_name)
        self.iam = self.boto_client.client("iam")

    def manage_iam(self, role_name: str, *args, **kwargs) -> str:
        if not self.check_iam_role_exists(role_name=role_name):
            role_response = self.create_iam(role_name, *args, **kwargs)
            return role_response["Role"]["Arn"]
        else:
            return self.get_iam_role_arn(role_name)

    def create_role(self, role_name: str, asssume_policy: str = None) -> dict:
        policy = asssume_policy if asssume_policy else self.assume_policy_str
        response = self.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=policy,
            Description="Autogenerated Propheto role for creating and managing ML API Services",
        )
        # NEED TO WAIT FOR ROLE TO GET CREATED
        waiter = self.iam.get_waiter("role_exists")
        waiter.wait(RoleName=role_name, WaiterConfig={"Delay": 5, "MaxAttempts": 30})
        return response

    def get_iam_role_arn(self, role_name: Optional[str] = "") -> str:
        role_name = role_name if role_name != "" else self.role_name
        iam_role = self.iam.get_role(RoleName=role_name)
        return iam_role["Role"]["Arn"]

    def check_iam_role_exists(self, role_name: str) -> bool:
        try:
            self.iam.get_role(RoleName=role_name)
            return True
        except self.iam.exceptions.NoSuchEntityException:
            return False

    def check_iam_policy_exists(
        self,
        policy_arn: Optional[str] = None,
        role_name: Optional[str] = None,
        policy_name: Optional[str] = None,
    ) -> bool:
        try:
            if not policy_arn:
                policy_name = policy_name if policy_name else f"{role_name}Policy"
                policy_arn = f"arn:aws:iam::{self.aws_account_id}:policy/{policy_name}"
            response = self.iam.get_policy(PolicyArn=policy_arn)
            return True
        except self.iam.exceptions.NoSuchEntityException:
            return False

    def create_iam(self, role_name: str, policy_name: Optional[str] = None) -> dict:
        role = self.create_role(role_name)
        policy_name = policy_name if policy_name else f"{role_name}Policy"
        if not self.check_iam_policy_exists(policy_name=policy_name):
            policy = self.create_policy(policy_name)
            policy_arn = policy["Policy"]["Arn"]
        else:
            policy_name = policy_name if policy_name else f"{role_name}Policy"
            policy_arn = f"arn:aws:iam::{self.aws_account_id}:policy/{policy_name}"
        reseponse = self.attach_policy(role_name, policy_arn)
        return role

    def create_policy(self, policy_name: str, attach_policy: str = None) -> dict:
        policy = attach_policy if attach_policy else self.attach_policy_str
        response = self.iam.create_policy(PolicyName=policy_name, PolicyDocument=policy)
        policy_arn = response["Policy"]["Arn"]
        # NEED TO WAIT FOR THE POLICY TO GET CREATED
        waiter = self.iam.get_waiter("policy_exists")
        waiter.wait(PolicyArn=policy_arn, WaiterConfig={"Delay": 5, "MaxAttempts": 30})
        return response

    def attach_policy(self, role_name: str, policy_arn: str) -> dict:
        response = self.iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        return response

    def delete_iam(self, role_name: str) -> dict:
        response = self.iam.delete_role(RoleName=role_name)
        # response = self.iam.delete_role_policy(RoleName, PolicyName)
        return response

    def destroy(self, role_name: str) -> dict:
        response = self.delete_iam(role_name)
        return response
