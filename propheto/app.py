import os
import json
import pickle
import base64
import logging
import inspect
from time import time
from warnings import warn
from datetime import date, datetime
from typing import Optional, Tuple, Any, List, Dict
from propheto.utilities import unique_id
from requests import session
from .package import (
    ZipService,
    APIService,
    VirtualEnvironment,
    ContainerEnvironment,
    ModelSerializer,
    CodeIntrospect,
)
from .deployments import AWS, GCP, Azure
from pathlib import Path
from .project import API, Configuration

logger = logging.getLogger(__name__)


PYTHON_ENVIRONMENT = os.path.dirname(inspect.getfile(inspect))


class Propheto:
    """
    Propheto class for creating and managing microservices in Production environments.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        experiment: str,
        credentials: dict,
        id: Optional[str] = "",
        current_iteration_id: Optional[str] = "",
        iterations: Optional[dict] = {},
        status: Optional[str] = "inactive",
        init_local: Optional[bool] = False,
        #profile_name: Optional[str] = "default",
        file_dir: Optional[str] = os.getcwd(),
        *args,
        **kwargs,
    ) -> None:
        self.project_name = name
        self.version = version
        self.experiment = experiment
        self.description = description
        self.id = id

        # Initialize services
        # Propheto API
        self.api = API(credentials=credentials, **kwargs)
        self.config = Configuration(
            id=self.id,
            name=name,
            version=version,
            description=description,
            current_iteration_id=current_iteration_id,
            iterations=iterations,
            **kwargs,
        )
        self._init_project(
            name=name,
            version=version,
            iterations=iterations,
            id=id,
            description=description,
            status=status,
            local=init_local,
            **kwargs,
        )
        # Initialize other propheto services
        # Classes to create ML services
        self.api_service = APIService(**kwargs)
        self.virtual_environment = VirtualEnvironment(**kwargs)
        self.zip_service = ZipService(**kwargs)
        self.container_environment = ContainerEnvironment(**kwargs)
        self.serializer = ModelSerializer(**kwargs)
        self.aws = AWS(**kwargs)
        self.code_introspecter = CodeIntrospect(file_dir=file_dir, **kwargs)
        self.working_directory = file_dir
        self.parent_dir, self.project_dir = self._generate_base_artifacts()

    def __repr__(self) -> str:
        return f"Propheto(id={self.id}, project_name={self.project_name}, version={self.version})"

    def __str__(self) -> str:
        return f"Propheto(id={self.id}, project_name={self.project_name}, version={self.version})"

    def _load_config(
        self, project: json, remote_profile_name: Optional[str] = "default"
    ) -> None:
        """
        
        """
        self.config = Configuration(**project)
        self.config.loads(profile_name=remote_profile_name)
        self.id = self.config.id

    def _create_project(
        self,
        name: str,
        version: str,
        iterations: list,
        description: str,
        status: str,
        current_iteration_id: str,
    ) -> None:
        """
        
        """
        payload = {
            "name": name,
            "version": version,
            "iterations": iterations,
            "description": description,
            "status": status,
            "current_iteration_id": current_iteration_id,
        }
        response = self.api.create_project(payload)
        self.id = response["data"]["id"]
        self.config.id = self.id

    def _init_project(
        self,
        name: str,
        version: str,
        iterations: list,
        id: str,
        description: str,
        status: str,
        local: bool = False,
        profile_name: Optional[str] = "default",
        *args,
        **kwargs,
    ) -> None:
        """
        Initialize the project against the Propheto API service.

        Parameters
        ----------
        name : str
                Project name for the specific project
        version : str
                Project version for the current iteration
        iterations : str
                Project iterations
        id : str
                String representing the unique project id
        description : str
                Project description
        local : bool, optional
                Whether or not to load the local configuration
        profile_name : str, optional
                Optional remote profile
        """
        self.config.id = self.id
        if "iteration_name" not in iterations:
            iterations["iteration_name"] = self.experiment
        self.config.add_iteration(**iterations, set_current=True)
        current_iteration_id = self.config.current_iteration_id
        iterations[current_iteration_id] = self.config.iterations[current_iteration_id].to_dict()
        if local:
            # Read the local propheto.config file
            # TODO: ACCEPT PATH PARAMETER FOR CONFIG
            current_directory = Path("")
            subdir_path = current_directory.joinpath(
                "propheto-package", "propheto.config"
            )
            current_dir_path = current_directory.joinpath("propheto.config")
            has_subdir = os.path.exists(subdir_path)
            filepath = subdir_path if has_subdir else current_dir_path
            with open(filepath, "r") as _config_file:
                config = json.load(_config_file)
            self._load_config(config, profile_name)
        else:
            # Get remote configuration
            if id != "":
                response_json = self.api.get_projects(project_id=id)
                if "error" not in response_json:
                    self._load_config(response_json["projects"][0], profile_name)
                else:
                    self._create_project(
                        name,
                        version,
                        iterations ,
                        description,
                        status,
                        current_iteration_id,
                    )
            elif name != "":
                response_json = self.api.get_projects(project_name=name)
                if "error" not in response_json and response_json["projects"] != []:
                    # TODO: HANDLE MULTIPLE MATCHES
                    self._load_config(response_json["projects"][0], profile_name)
                else:
                    self._create_project(
                        name,
                        version,
                        iterations,
                        description,
                        status,
                        current_iteration_id,
                    )
            else:
                raise Exception("Project name or project id are required fields.")

    def _create_directory(self) -> str:
        DIR_PATH = Path(self.working_directory, "propheto-package")
        DIR_PATH.mkdir(parents=True, exist_ok=True)
        os.chdir(DIR_PATH)
        return DIR_PATH.absolute()

    def model(self, action: str, *args, **kwargs) -> None:
        """
        Method to track the model definition and model training actions

        Parameters
        ----------
        action : str, required
                Model action to tracked with Propheto
        """
        if action == "define":
            pass
        elif action == "train":
            pass
        else:
            pass

    def log(
        self,
        key: str,
        data: Any,
        type: Optional[str] = None,
        annotate: Optional[str] = None,
        ignore_warnings: Optional[bool] = False,
        *args,
        **kwargs,
    ) -> None:
        """
        Create local log for current deployment and setup logging ability for 
        models deployed into production infrastructure.
        
        Parameters
        ----------
        data : required
                The data which will be logged from Propheto
        type : str, optional
                Annotation/logging type 
        annotate : str, optional
                Title/name for the log resource
        """
        local_log_path = Path(self.working_directory, "propheto-package/logs")
        local_log_path.mkdir(parents=True, exist_ok=True)
        filepath = local_log_path.absolute()
        key = key.replace(" ", "_")
        filename = f"propheto-log-{key}.json"
        if Path(filepath, filename).exists():
            warn("Warning filename already exists")
        js_data = {}
        js_data["annotation"] = annotate
        js_data["created_at"] = datetime.fromtimestamp(time()).isoformat()
        if type == "table":
            data = data.to_html(index=False)
            log_type = "table"
        elif type == "plot":
            # TODO: CHANGE TO USE TEMPFILE
            plot_filename = Path(filepath, f"propheto-log-{key}.png")
            data.savefig(plot_filename)
            with open(plot_filename, "rb") as plot_file:
                data = base64.b64encode(plot_file.read()).decode("utf-8")
            os.remove(plot_filename)
            log_type = "plot"
        elif type == "float":
            data = float(data)
            log_type = "float"
        elif type == "string":
            data = str(data)
            log_type = "string"
        else:
            message = f"Unsupported type: {type}. Supported types are 'table', 'plot', 'float', 'string'. Please chose a type from this list."
            raise Exception(message)
        js_data["data"] = data
        js_data["log_type"] = log_type
        with open(Path(filepath, filename), "w") as data_file:
            json.dump(js_data, data_file)

    def monitor(self, *args, **kwargs) -> None:
        """
        Set up a metric to monitor over time. 
        """
        pass

    def alert(self, conditional, target, *args, **kwargs) -> None:
        """
        Create an alert and a method to check for alert
        """
        pass

    def destroy(
        self, iteration_id: Optional[str] = None, options_args: Optional[dict] = {}
    ) -> None:
        """
        Destroy target resources
        """
        iteration_id = (
            iteration_id if iteration_id else self.config.current_iteration_id
        )
        if options_args != {}:
            if "excludes" in options_args:
                excludes = options_args["excludes"]
                self.config.destroy(iteration_id, excludes=excludes)
            elif "includes" in options_args:
                includes = options_args["includes"]
                self.config.destroy(iteration_id, includes=includes)
        else:
            self.config.destroy(iteration_id)
            self.config.iterations[self.config.current_iteration_id].set_status(
                "inactive"
            )
            self.config.status = "inactive"

        # Write config locally to project folder
        DIR_PATH = Path(self.working_directory, "propheto-package")
        os.chdir(DIR_PATH)
        self.config.write_config()
        os.chdir(self.working_directory)
        # Update the project config in Propheto
        self.api.update_project(project_id=self.id, payload=self.config.to_dict())
        # TODO: UPDATE ALL THE REMOTE API RESOURCES STATUS AS WELL

    def generate(
        self,
        model: object,
        target: str,
        deployment_type: str = "realtime-serverless",
        *args,
        **kwargs,
    ) -> str:
        """
        Generate the output artifacts for the microservice. These can then be added into production manually or via a CI/CD process.

        Parameters
        ----------
        model : object,
                Trained model object to be deployed
        target : str,
                Target specification for the deployment
        deployment_type : str,
                Deployment type for the service. 
        """
        self._validate_target(target)
        if target == "aws":
            self._deploy_aws(model, target, action="generate")
        elif target == "gcp":
            return "GCP deployments are currently still under development. Please contact support team at hello@propheto.io for more details."
        elif target == "azure":
            return "Azure deployments are currently still under development. Please contact support team at hello@propheto.io for more details."
        else:
            raise Exception(
                "Please specify a target cloud deployment: AWS, GCP, or Azure"
            )

    def deploy(
        self,
        model: object,
        target: str,
        deployment_type: Optional[str] = "realtime-serverless",
        if_exists: Optional[str] = "update",
        *args,
        **kwargs,
    ) -> None:
        """
        Take a trained model object and deploy it to a cloud environment.

        Parameters
        ----------
        model : object, required
                Trained model object to be deployed
        target : str, required
                Target specification for the deployment
        deployment_type : str, optional
                Deployment type for the service. 
        if_exists : str, optional
                Determine what to do if resource already exists
        """
        # Read notebook
        # TODO: generalize to read code not notebook
        self.code_introspecter.get_notebook_details()
        _ = self.code_introspecter.read_notebook()
        _ = self.code_introspecter.get_notebook_code_cells()
        self._validate_target(target)
        if target == "aws":
            self._deploy_aws(model, action="deploy")
        elif target == "gcp":
            return "GCP deployments are currently still under development. Please contact support team at hello@propheto.io for more details."
        elif target == "azure":
            return "Azure deployments are currently still under development. Please contact support team at hello@propheto.io for more details."
        elif target == "local":
            return "Local deployments are currently still under development. Please contact support team at hello@propheto.io for more details."
        else:
            raise Exception(
                "Please specify a target cloud deployment: AWS, GCP, or Azure"
            )
        self.config.iterations[self.config.current_iteration_id].set_status("active")

    def _deploy_aws_cloudformation(self, model: object, target: str) -> None:
        """
        Take model input then deploy to AWS behind a cloudformation template.
        """
        # TODO: CREATE S3 FOR MODEL RESOURCES
        # TODO: WRITE CLOUDFORMATION VARIABLES FROM RESOURCES
        project_name = self.project_name.replace(" ", "").lower()
        project_name += unique_id(length=4, has_numbers=False).lower()
        self.aws.deploy_cloudformation(project_name)

    def _deploy_aws_zip_environment(self, model: object, target: str) -> None:
        """
        Deploy a virtual environment to AWS
        """
        pass

    def _store_model(self, model: object) -> str:
        """
        Save the model.
        """
        file_dir = os.getcwd()
        filepath = f"{file_dir}"
        self.serializer.save_model(model, save_path=filepath)
        model_filename = self.serializer.file_path
        (
            model_serializer,
            model_preprocessor,
            model_predictor,
            model_postprocessor,
        ) = self.serializer.get_model_processing_code()
        # serialization_code, preprocessing_code, predict_code, postprocessing_code
        model_type = self.serializer.model_type
        return (
            model_filename,
            model_serializer,
            model_type,
            model_preprocessor,
            model_predictor,
            model_postprocessor,
        )

    def _generate_base_artifacts(self) -> Tuple[str]:
        """
        Generate the base artifacts for the models
        """
        # TODO: CHECK IF DIRECTORY EXISTS
        parent_dir = self.working_directory
        project_dir = self._create_directory()
        print("Created project directory...")
        return parent_dir, project_dir

    def _deploy_aws(self, model: object, action: str = "deploy") -> None:
        """
        Take a model as an input then deploy to AWS directly environment.

        Parameters
        ----------
        model : object, required
                The trained model object that will be deployed
        action : str, optional
                Optional parameter specifying what type of action is to be performed
        """
        # Check iterations, if one exists for current id, add new one to config
        if self.config.iterations[self.config.current_iteration_id].resources != {}:
            self.config.add_iteration(iteration_name=self.experiment, set_current=True)
            current_iteration_id = self.config.current_iteration_id
        # parent_dir, project_dir = self._generate_base_artifacts()
        (
            model_filepath,
            model_serializer,
            model_type,
            model_preprocessor,
            model_predictor,
            model_postprocessor,
        ) = self._store_model(model)
        project_name_formatted = self.project_name.replace(" ", "").lower()
        # CREATE VIRTUAL ENVIRONMENT
        # virtualenv = self.virtual_environment.generate_environment()
        # print("Created virtual environment...")

        # CREATE IAM / ROLE
        aws_account_id = self.aws.aws_account_id
        role_arn = f"arn:aws:iam::{aws_account_id}:role/ProphetoAutoBuild"
        role_arn = self.aws.iam.manage_iam(role_name="ProphetoAutoBuild")
        # CREATE ECR REPOSITORY
        ecr_repository_name = (
            "propheto-" + unique_id(length=4, has_numbers=False).lower()
        )
        if action == "deploy":
            ecr_response = self.aws.ecr.create_ecr_repository(
                repository_name=ecr_repository_name
            )
            print("Created ECR Repository...")
        self.config.add_resource(
            remote_object=self.aws.ecr, id=ecr_repository_name, name="ECR"
        )

        # CREATE BUCKET & FORMAT NAME
        s3_bucket_name = self.project_name.replace(" ", "")
        for number in range(10):
            s3_bucket_name = s3_bucket_name.replace(str(number), "")
        if action == "deploy":
            s3_bucket_name = self.aws.s3.create_bucket(self.project_name)
            print("Created S3 bucket...")

        self.config.add_resource(
            remote_object=self.aws.s3, id=s3_bucket_name, name="S3"
        )

        # UPLOAD MODEL PACKAGE
        s3_model_path = ""
        if action == "deploy":
            _model_filename = model_filepath.parts[-1]
            print(_model_filename)
            s3_model_path = self.aws.s3.upload_file(
                project_name=self.project_name.replace(" ", ""),
                source_path=model_filepath.as_posix(),
                filename=_model_filename,
            )
            print("Uploaded ML model...")

        # UPLOAD LOGS
        if action == "deploy":
            log_path = Path(self.working_directory, "propheto-package", "logs")
            s3_response = self.aws.s3.upload_folder(
                project_name=self.project_name.replace(" ", ""),
                local_folder_path=log_path,
                output_folder_path="logs",
            )
            print("Uploaded local logs")

        # GENERATE API CODE
        app_directory = self.api_service.generate_service(
            bucket_name=s3_bucket_name,
            object_key=s3_model_path,
            model_serializer=model_serializer,
            model_preprocessor=model_preprocessor,
            model_predictor=model_predictor,
            model_postprocessor=model_postprocessor,
            project_name=self.project_name.replace(" ", ""),
        )
        print("Generated App Service...")

        # CREATE CONTAINER ENVIRONMENT
        region = self.aws.region
        self.container_environment.generate_environment(
            file_directory=app_directory,
            ecr_repo=ecr_repository_name,
            aws_account_id=aws_account_id,
            model_type=model_type,
            region=region,
        )

        # ZIP SERVICE
        self.zip_service.package_project(app_dir=self.project_dir)
        print("Zipped service...")

        # UPLOAD ZIP PACKAGE
        if action == "deploy":
            s3_zip_path = self.aws.s3.upload_file(
                filename="lambda.zip", project_name=self.project_name.replace(" ", "")
            )
            print("Uploaded zipped service...")

        # CREATE CODEBUILD PROJECT
        project_name = "propheto-" + unique_id(length=4, has_numbers=False).lower()
        project_description = "Propheto API Autogenerated for ML service."
        service_role_arn = role_arn
        if action == "deploy":
            code_location = f"{s3_bucket_name}/{s3_zip_path}"
            project_response = self.aws.code_build.create_project(
                str(project_name),
                str(project_description),
                str(service_role_arn),
                str(code_location),
            )
        self.config.add_resource(
            remote_object=self.aws.code_build, id=project_name, name="CodeBuild",
        )

        # RUN CODEBUILD FROM S3
        if action == "deploy":
            build_response = self.aws.code_build.build_image(project_name)

            # GET ARN FOR ECR IMAGE
            image_uri = self.aws.ecr.get_ecr_image_uri(ecr_repository_name)

        # CREATE LAMBDA FUNCTION
        function_name = (
            project_name_formatted + "-" + unique_id(length=4, has_numbers=False)
        ).lower()
        if action == "deploy":
            self.aws.aws_lambda.create_lambda_function(
                function_name, role_arn, image_uri=image_uri,
            )
            print("Created lambda function...")

        self.config.add_resource(
            remote_object=self.aws.aws_lambda, id=function_name, name="AWSLambda",
        )
        lambda_arn = self.aws.aws_lambda.get_lambda_arn(function_name)
        region = self.aws.api_gateway.region
        uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        # CREATE API
        #  https://{rest_api_id}.execute-api.{region}.amazonaws.com/{stage}
        if action == "deploy":
            self.aws.api_gateway.create_api(
                project_name_formatted, self.description, self.version, uri
            )
            print("Created API...")

        self.config.add_resource(
            remote_object=self.aws.api_gateway,
            id=project_name_formatted,
            name="APIGateway",
        )

        # PROVISION ACCESS
        if action == "deploy":
            self.aws.aws_lambda.grant_lambda_permission(
                self.aws.api_gateway.rest_api_id, function_name
            )

            # DEPLOY API
            api_url = self.aws.api_gateway.create_deployment(
                stage_name="dev",
                stage_description="Developent deployment",
                description="Deployment",
            )
            self.config.service_api_url = api_url
            print("Deployed API! - ", api_url)
        
        # SCHEDULE KEEP WARM
        rule_name = "Propheto-Keepwarm-{0}".format(unique_id())
        if action == "deploy":
            response = self.aws.cloudwatch.create_keepwarm_event(
                rule_name=rule_name,
                role_arn=role_arn,
                lambda_arn=lambda_arn
            )
            rule_arn = response['RuleArn']

            self.aws.aws_lambda.lambda_client.add_permission(
                FunctionName=function_name,
                Action="lambda:InvokeFunction",
                SourceArn=rule_arn,
                Principal="events.amazonaws.com",
                StatementId="Propheto-{0}".format(unique_id())
            )
            print("Created Cloudwatch Keepwarm...")
        
        self.config.add_resource(
            remote_object=self.aws.cloudwatch,
            id=rule_name,
            name="Cloudwatch",
        )


        project_url = f"https://app.getpropheto.com/projects/{self.id}"
        print(f"Check out your project in Propheto at: {project_url}")
        # DEPLOY TO AWS
        self.config.iterations[self.config.current_iteration_id].set_status("active")
        self.config.status = "active"

        # Write config locally to project folder
        self.config.write_config()

        # Update the project config in Propheto
        self.api.update_project(project_id=self.id, payload=self.config.to_dict())

        # Navigate back to parent dir
        os.chdir(self.parent_dir)

    def _validate_target(self, target: str) -> None:
        target = target.lower().strip()
        if target not in ["aws", "gcp", "azure"]:
            raise Exception(
                "Please specify a target cloud deployment: AWS, GCP, or Azure"
            )
        else:
            pass

    def update(self, actions: dict, *args, **kwargs,) -> None:
        """
        Update a deployed model for various resources

        Parameters
        ----------
        actions : dict, required
                Required parameter specifying the type(s) of action(s) is to be performed. 
                Options are 'model', 'api', 'logs', where 'api' is a list with some arguments  
        model : object, optional
                The trained model object that will be deployed. Required if the action type is related to the model
        """
        ## ADD OPTION TO UPDATE NEW LOGS
        if "model" in actions:
            model = actions["model"]
            model_filepath, _, _, _, _, _ = self._store_model(model)
            project_name = self.project_name.replace(" ", "")
            # UPLOAD MODEL PACKAGE
            _model_filename = model_filepath.parts[-1]
            print(_model_filename)
            s3_model_path = self.aws.s3.upload_file(
                project_name=project_name,
                source_path=model_filepath.as_posix(),
                filename=_model_filename,
            )
            print("Uploaded ML model...")
        elif "logs" in actions:
            log_path = Path(self.working_directory, "propheto-package", "logs")
            project_name = self.project_name.replace(" ", "")
            s3_response = self.aws.s3.upload_folder(
                project_name=project_name,
                local_folder_path=log_path,
                output_folder_path="logs",
            )
            print("Uploaded local logs")
        elif "api" in actions:
            # API ACTIONS SHOULD BE A DICTIONARY
            if "generate_service" in actions["api"]:
                # GENERATE API CODE
                s3_bucket_name = self.aws.s3.s3_bucket_name
                s3_model_path = self.aws.s3.object_key  # TODO: GET NAME
                model_serializer = ""  # TODO: GET NAME
                model_preprocessor = ""  # TODO: GET NAME
                model_predictor = ""  # TODO: GET NAME
                model_postprocessor = ""  # TODO: GET NAME
                app_directory = self.api_service.generate_service(
                    bucket_name=s3_bucket_name,
                    object_key=s3_model_path,
                    model_serializer=model_serializer,
                    model_preprocessor=model_preprocessor,
                    model_predictor=model_predictor,
                    model_postprocessor=model_postprocessor,
                    project_name=self.project_name.replace(" ", ""),
                )
                print("Generated App Service...")

                # CREATE CONTAINER ENVIRONMENT
                region = self.aws.region
                aws_account_id = self.aws.aws_account_id
                ecr_repository_name = self.aws.ecr.ecr_repository_name
                model_type = ""  # TODO: GET NAME
                self.container_environment.generate_environment(
                    file_directory=app_directory,
                    ecr_repo=ecr_repository_name,
                    aws_account_id=aws_account_id,
                    model_type=model_type,
                    region=region,
                )
            elif "deploy_service" in actions["api"]:
                # ZIP SERVICE
                self.zip_service.package_project(app_dir=self.project_dir)
                print("Zipped service...")

                bucket_name = self.aws.s3.s3_bucket_name
                project_name = self.project_name.replace(" ", "")
                object_key = f"{project_name}/lambda.zip"
                # Delete zipfile
                response = self.aws.s3.delete_object(
                    bucket_name=bucket_name, object_key=object_key
                )
                # upload new file
                s3_zip_path = self.aws.s3.upload_file(
                    filename="lambda.zip", project_name=project_name,
                )
                print("Uploaded zipped service...")

                # RUN CODEBUILD FROM S3
                project_name = self.aws.code_build.project_name
                build_response = self.aws.code_build.build_image(project_name)
                ecr_repository_name = self.aws.ecr.ecr_repository_name
                # GET ARN FOR ECR IMAGE
                image_uri = self.aws.ecr.get_ecr_image_uri(ecr_repository_name)

                # CREATE LAMBDA FUNCTION
                project_name_formatted = self.project_name.replace(" ", "").lower()
                function_name = self.aws.aws_lambda.function_name
                self.aws.aws_lambda.update_lambda_function(
                    function_name, image_uri=image_uri
                )
                print("Updated lambda function...")
                # DEPLOY API
                api_url = self.aws.api_gateway.service_api_url
                print("Deployed API! - ", api_url)
                project_url = f"https://app.getpropheto.com/projects/{self.id}"
                print(f"Check out your project in Propheto at: {project_url}")
            else:
                raise Exception("Please specify exactly the action")
