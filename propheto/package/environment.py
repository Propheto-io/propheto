# Environment class
import os
import pathlib
import inspect
import signal
import subprocess
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

PYTHON_ENVIRONMENT = os.path.dirname(inspect.getfile(inspect))
PYTHON_VERSION = Path(PYTHON_ENVIRONMENT).parts[-1]
PYTHON_VERSION_NUMBER = PYTHON_VERSION.lower().replace('python', '')

# python: 3.8
BUILDSPEC_YAML = """version: 0.2

env:
  shell: bash
  variables:
    DOCKER_FILE_NAME: 'Dockerfile'
    CONTAINER_TO_RELEASE_NAME: 'propheto-ml'
    REPOSITORY_URI: '%{{AWS_ACCOUNT_ID}}%.dkr.ecr.%{{AWS_REGION}}%.amazonaws.com/%{{AWS_ECR}}%'

phases:
  install:
    runtime-versions:
      python: %{PYTHON_VERSION_NUMBER}%
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws --version
      - ls -l
      - pwd
      - $(aws ecr get-login --region $AWS_DEFAULT_REGION --no-include-email)
      - echo Target Docker image tag - TEST
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
      - echo CODEBUILD VERSION $CODEBUILD_RESOLVED_SOURCE_VERSION
  build:
    commands:
      - echo "Starting Docker build `date` in `pwd`"
      - docker build -t $REPOSITORY_URI:latest -f $DOCKER_FILE_NAME .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo "Pushing to repo uri $REPOSITORY_URI"
      - docker push "${REPOSITORY_URI}:latest"
      - echo "Pushing to image uri $IMAGE_URI"
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo "--------BUILD DONE.--------"

cache:
  paths:
    - '/root/.cache/pip'""".replace('%{PYTHON_VERSION_NUMBER}%', PYTHON_VERSION_NUMBER)


# FROM public.ecr.aws/lambda/python:3.8
DOCKERFILE_TEXT = f"""# LAMBDA ECR
FROM public.ecr.aws/lambda/python:{PYTHON_VERSION_NUMBER}

RUN /var/lang/bin/python{PYTHON_VERSION_NUMBER} -m pip install --upgrade pip

COPY . .

RUN pip install -r requirements.txt 

CMD ["main.handler"]"""

## SKLEARN
SKLEARN_REQUIREMENTS_TEXT = """asgiref==3.4.1
boto3==1.17.112
botocore==1.20.112
click==8.0.1
fastapi==0.66.0
h11==0.12.0
jmespath==0.10.0
joblib==1.0.1
mangum==0.11.0
numpy==1.21.0
pandas==1.3.0
pydantic==1.8.2
python-dateutil==2.8.2
pytz==2021.1
s3transfer==0.4.2
scikit-learn==1.0
scikit-plot==0.3.7
scipy==1.7.0
six==1.16.0
starlette==0.14.2
threadpoolctl==2.2.0
typing-extensions==3.10.0.0
urllib3==1.26.6
uvicorn==0.14.0"""

# ## TENSORFLOW
TENSORFLOW_REQUIREMENTS_TEXT = """absl-py==0.13.0
astunparse==1.6.3
boto3==1.18.31
botocore==1.21.31
cachetools==4.2.2
certifi==2021.5.30
charset-normalizer==2.0.4
clang==5.0
fastapi==0.68.1
flatbuffers==1.12
gast==0.4.0
google-auth==1.35.0
google-auth-oauthlib==0.4.5
google-pasta==0.2.0
grpcio==1.39.0
h5py==3.1.0
idna==3.2
jmespath==0.10.0
keras==2.6.0
Keras-Preprocessing==1.1.2
mangum==0.12.2
Markdown==3.3.4
numpy==1.19.5
oauthlib==3.1.1
opt-einsum==3.3.0
protobuf==3.17.3
pyasn1==0.4.8
pyasn1-modules==0.2.8
pydantic==1.8.2
python-dateutil==2.8.2
requests==2.26.0
requests-oauthlib==1.3.0
rsa==4.7.2
s3transfer==0.5.0
six==1.15.0
starlette==0.14.2
tensorboard==2.6.0
tensorboard-data-server==0.6.1
tensorboard-plugin-wit==1.8.0
tensorflow==2.6.0
tensorflow-estimator==2.6.0
termcolor==1.1.0
typing-extensions==3.7.4.3
urllib3==1.26.6
Werkzeug==2.0.1
wrapt==1.12.1"""

## PYTORCH
PYTORCH_REQUIREMENTS_TEXT = """cloudpickle==1.6.0
fastapi==0.68.1
mangum==0.12.2
numpy==1.21.2
pandas==1.3.2
pydantic==1.8.2
python-dateutil==2.8.2
pytz==2021.1
six==1.16.0
starlette==0.14.2
torch==1.9.0
typing-extensions==3.10.0.0
boto3==1.17.112
botocore==1.20.112"""

## PYTORCH
XGBOOST_REQUIREMENTS_TEXT = """boto3==1.18.41
botocore==1.21.41
cloudpickle==2.0.0
fastapi==0.68.1
jmespath==0.10.0
mangum==0.12.2
numpy==1.21.2
pydantic==1.8.2
python-dateutil==2.8.2
s3transfer==0.5.0
scipy==1.7.1
six==1.16.0
starlette==0.14.2
typing-extensions==3.10.0.2
urllib3==1.26.6
xgboost==1.4.2
scikit-learn==0.24.2"""


class EnvironmentBase:
    """
    Base environment for virtual and container environments
    """

    docker = DOCKERFILE_TEXT
    sklearn_requirements = SKLEARN_REQUIREMENTS_TEXT
    pytorch_requirements = PYTORCH_REQUIREMENTS_TEXT
    tensorflow_requirements = TENSORFLOW_REQUIREMENTS_TEXT
    xgboost_requirements = XGBOOST_REQUIREMENTS_TEXT
    buildspec = BUILDSPEC_YAML

    def __init__(self) -> None:
        pass


class VirtualEnvironment(EnvironmentBase):
    """
    Automatically create a virtual environment
    """

    def __init__(
        self, 
        parent_dir: Optional[str] = "",
        environment_directory: Optional[str] = "", 
        environment: Optional[str] = "", 
        *args, 
        **kwargs
    ) -> None:
        super().__init__()
        self.parent_dir = parent_dir
        self.environment_directory = environment_directory
        self.environment = environment
        self.server_pro = None
        self.remote_server_pro = None

    def create_environment(self, name: Optional[str] = "env") -> None:
        """
        Create a virtual environment.
        """
        print(self.environment_directory)
        os.chdir(self.environment_directory)
        self.environment = name
        cmd = f"python3 -m venv {self.environment}"
        subprocess.call(cmd, shell=True, executable="/bin/bash")
        os.chdir(self.parent_dir)


    def install_packages(self, extra_packages: str = None) -> None:
        """
        Install the required packages into the virtual environment.
        """
        # cmd = f"source {self.environment}/bin/activate; pip install fastapi uvicorn[standard] mangum boto3"
        os.chdir(self.environment_directory)
        cmd = (
            f"source {self.environment}/bin/activate; pip install -r requirements.txt;"
        )
        if extra_packages:
            cmd = cmd + f"pip install {extra_packages}"
        subprocess.call(cmd, shell=True, executable="/bin/bash")
        os.chdir(self.parent_dir)
        

    def start_server(self) -> None:
        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and before  exec() to run the shell.
        os.chdir(self.environment_directory)
        cmd = f"source {self.environment}/bin/activate; cd api; uvicorn main:app --reload"
        pro = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            shell=True,
            preexec_fn=os.setsid,
            executable="/bin/bash",
        )
        self.server_pro = pro
        os.chdir(self.parent_dir)
    
    def expose(self):
        cmd = "ssh -R 80:localhost:8000 localhost.run"
        pro = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            shell=True,
            preexec_fn=os.setsid,
            executable="/bin/bash",
        )
        self.remote_server_pro = pro

    def kill_server(self, pid: Optional[str] = "") -> None:
        pid = pid if pid != "" else self.server_pro.pid
        os.killpg(os.getpgid(pid), signal.SIGTERM)  # Send the signal to all the process groups

    def generate_environment(
        self,
        name: Optional[str] = "env",
        file_directory: Optional[str] = "",
        model_type: Optional[str] = "sklearn",
        requirements_txt: Optional[str] = "",
    ) -> str:
        """
        Parent method to generate the environment.
        """
        self.create_environment(name)
        file_directory = file_directory if file_directory != "" else self.environment_directory
        print("Creating Dockerfile...")
        with open(Path(file_directory, "Dockerfile"), "w") as docker_file:
            docker_file.write(self.docker)
        print("Creating requirements...")
        with open(Path(file_directory, "requirements.txt"), "w") as requirements_file:
            if requirements_txt == "":
                if model_type == "sklearn":
                    requirements_file.write(self.sklearn_requirements)
                elif model_type == "pytorch":
                    requirements_file.write(self.pytorch_requirements)
                elif model_type == "tensorflow":
                    requirements_file.write(self.tensorflow_requirements)
                elif model_type == "xgboost":
                    requirements_file.write(self.xgboost_requirements)
            else:
                raise Exception(
                    "Model type {model_type} is unsupported. Please use a different model type."
                )
                # requirements_file.write(requirements_txt)
        self.install_packages()
        return self.environment


# Docker Class and requirements.txt
class ContainerEnvironment(EnvironmentBase):
    """
    Container environment
    """

    def __init__(self, environment: Optional[str] = "", *args, **kwargs) -> None:
        super().__init__()
        self.environment = environment

    def generate_environment(
        self,
        file_directory: str,
        ecr_repo: str,
        aws_account_id: str,
        region: str = "us-east-1",
        model_type: str = "sklearn",
        requirements_txt: str = "",
    ) -> str:
        """
        Generate the container environment.
        """
        # TODO: REMOVE AWS REGION
        print("Creating Dockerfile...")
        with open(Path(file_directory, "Dockerfile"), "w") as docker_file:
            docker_file.write(self.docker)
        print("Creating requirements...")
        with open(Path(file_directory, "requirements.txt"), "w") as requirements_file:
            if requirements_txt == "":
                if model_type == "sklearn":
                    requirements_file.write(self.sklearn_requirements)
                elif model_type == "pytorch":
                    requirements_file.write(self.pytorch_requirements)
                elif model_type == "tensorflow":
                    requirements_file.write(self.tensorflow_requirements)
                elif model_type == "xgboost":
                    requirements_file.write(self.xgboost_requirements)
            else:
                raise Exception(
                    "Model type {model_type} is unsupported. Please use a different model type."
                )
                # requirements_file.write(requirements_txt)
        print("Creating buildspec...")
        with open(Path(file_directory, "buildspec.yml"), "w") as buildspec_file:
            buildspec_yaml = self.buildspec.replace(
                "%{{AWS_ACCOUNT_ID}}%", aws_account_id
            )
            buildspec_yaml = buildspec_yaml.replace("%{{AWS_REGION}}%", region)
            buildspec_yaml = buildspec_yaml.replace("%{{AWS_ECR}}%", ecr_repo)
            buildspec_file.write(buildspec_yaml)
