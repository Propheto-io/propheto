from ...utilities import unique_id
from .boto_session import BotoInterface
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# # Create CloudWatchEvents client
# cloudwatch_events = boto3.client('events')

# # Put an event rule
# response = cloudwatch_events.put_rule(
#     Name='DEMO_EVENT',
#     RoleArn='IAM_ROLE_ARN',
#     ScheduleExpression='rate(5 minutes)',
#     State='ENABLED'
# )
# print(response['RuleArn'])

# import boto3

# # Create CloudWatchEvents client
# cloudwatch_events = boto3.client('events')

# # Put target for rule
# response = cloudwatch_events.put_targets(
#     Rule='DEMO_EVENT',
#     Targets=[
#         {
#             'Arn': 'LAMBDA_FUNCTION_ARN',
#             'Id': 'myCloudWatchEventsTarget',
#         }
#     ]
# )
# print(response)


class CloudWatch(BotoInterface):
    """
    Cloudwatch for scheduling lambdas.
    """

    def __init__(
        self,
        profile_name: Optional[str] = "default",
        region: Optional[str] = "us-east-1",
        rule_name: Optional[str] = "",
        *args,
        **kwargs,
    ) -> None:
        pass
        super().__init__(profile_name=profile_name, region=region)
        self.cloudwatch_events = self.boto_client.client("events")
        self.profile_name = profile_name
        self.region = region
        self.rule_name = rule_name

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        output_dict["rule_name"] = self.rule_name
        return output_dict

    def __repr__(self) -> str:
        if self.rule_name != "":
            return f"CloudWatch(profile_name={self.profile_name}, rule_name={self.rule_name})"
        else:
            return f"CloudWatch(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.rule_name != "":
            return f"CloudWatch(profile_name={self.profile_name}, rule_name={self.rule_name})"
        else:
            return f"CloudWatch(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "cloudwatch_events"]:
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
        """
        super().__init__(profile_name=profile_name, region=region)
        self.cloudwatch_events = self.boto_client.client("events")

    def destroy(self, rule_name: Optional[str] = "") -> dict:
        """
        Destroy the given S3 bucket. First need to empty it of contents then delete the bucket

        Parameters
        ----------
        rule_name : str, optional
                Event rule name which will be destroyed

        Returns
        -------
        delete_response : dict
                Response object from s3 client delete bucket command
        """
        rule_name = rule_name if rule_name != "" else self.rule_name
        targets = self.cloudwatch_events.list_targets_by_rule(Rule=rule_name)
        targets_ids = [target['Id'] for target in targets['Targets']]
        remove_response = self.cloudwatch_events.remove_targets(Rule=rule_name, Ids=targets_ids)
        delete_response = self.cloudwatch_events.delete_rule(Name=rule_name)
        return delete_response

    def create_keepwarm_event(
        self,
        rule_name: str,
        role_arn: str,
        lambda_arn: str,
        id: Optional[str] = "",
        schedule_exprn: Optional[str] = "rate(5 minutes)",
    ) -> dict:
        """
        Create a lambda keepwarm event

        """
        ruleResponse = self.create_rule(rule_name, role_arn, schedule_exprn)
        ruleTargetResponse = self.create_rule_target(rule_name, lambda_arn, id)
        return ruleResponse

    def create_rule(
        self,
        rule_name: str,
        role_arn: str,
        schedule_exprn: Optional[str] = "rate(5 minutes)",
    ) -> dict:
        """
        Create a rule event.
        """
        self.rule_name = rule_name
        response = self.cloudwatch_events.put_rule(
            Name=rule_name,
            RoleArn=role_arn,
            ScheduleExpression=schedule_exprn,
            State="ENABLED",
        )
        return response

    def create_rule_target(
        self,
        rule_name: str,
        lambda_arn: str,
        id: Optional[str] = "",
    ) -> dict:
        """
        Create a rule target which is the lambda to execute on the scheduled interval

        Parameters
        ----------
        name : str, required
                Name for the rule
        
        """
        id = id if id != "" else "Propheto-{0}".format(unique_id())
        # Put target for rule
        response = self.cloudwatch_events.put_targets(
            Rule=rule_name, Targets=[{"Arn": lambda_arn, "Id": id}],
        )
        return response

