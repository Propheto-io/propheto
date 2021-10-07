from ..utilities import copytree, human_size
import tempfile
import zipfile
import os
import shutil
import logging

logger = logging.getLogger(__name__)


ZIP_EXCLUDES = [
    "*.exe",
    "*.DS_Store",
    "*.Python",
    "*.git",
    ".git/*",
    "*.zip",
    "*.tar.gz",
    "*.hg",
    "pip",
    "docutils*",
    "setuputils*",
    "__pycache__/*",
]

ZIP_CODEBUILD_EXCLUDES = [
    # IF DOING CODEBUILD EXCLUDE VENV
    "env/*"
    ".env/*"
    ".venv/*"
    "venv/*"
]


class ZipService:
    """
    Manage and package the python project
    """

    def __init__(
        self,
        app_directory: str = None,
        zip_filename: str = "lambda.zip",
        zip_codebuild: bool = True,
        *args,
        **kwargs
    ) -> None:
        self.app_directory = app_directory if app_directory else os.getcwd()
        self.zip_filename = zip_filename
        self.temp_dir = None
        self.zip_codebuild = zip_codebuild  # ZIP PROJECT FOR CODEBUILD

    def create_temp_directory(self, prefix: str = "propheto-package") -> str:
        """
        Generate a temporary directory. 
        """
        temp_project_path = tempfile.mkdtemp(prefix=prefix)
        self.temp_dir = temp_project_path
        return temp_project_path

    def copy_directory(self, source_path: str, target_path: str = None) -> None:
        """
        Copy the files into the directory
        """
        source_path = source_path if source_path else self.app_directory
        target_path = target_path if target_path else self.temp_dir
        ## COPY THE PACKAGE FILES
        excludes = ZIP_EXCLUDES
        excludes += ZIP_CODEBUILD_EXCLUDES if self.zip_codebuild else []
        ignore = shutil.ignore_patterns(*excludes)
        copytree(
            source_path, target_path, metadata=False, symlinks=False, ignore=ignore,
        )

    def zip_directory(self, zip_filename: str = None, file_dir: str = None) -> str:
        """
        Zip the directory 
        """
        zip_filename = zip_filename if zip_filename else self.zip_filename
        file_dir = file_dir if file_dir else self.temp_dir
        # Assign the name of the directory to zip
        # writing files to a zipfile
        zip_file = zipfile.ZipFile(zip_filename, "w")
        with zip_file:
            # Read all directory, subdirectories and file lists
            for root, dirs, files in os.walk(file_dir):
                for file in files:
                    # Create the full filepath by using os module.
                    zip_file.write(
                        os.path.join(root, file),
                        arcname=os.path.join(root.replace(file_dir, ""), file),
                        compress_type=zipfile.ZIP_DEFLATED,
                    )
        return zip_filename

    def package_project(self, app_dir: str = None) -> str:
        """
        Create a package for the project.
        """
        temp_project_path = self.create_temp_directory()
        # TODO: FIGURE OUT WAY TO PARSE THE ENVIRONMENT AND PYTHON VERSION
        app_dir = app_dir if app_dir else self.app_directory
        # COPY THE VIRTUAL ENVIRONMENT
        # IF DOING VIRTUAL ENV ZIP THEN INCLUDE SITEPACKAGES
        if not self.zip_codebuild:
            packages_dir = app_dir + "/env/lib/python3.7/site-packages"
            self.copy_directory(source_path=packages_dir, target_path=temp_project_path)
        # COPY THE APPLICATION DIRECTORY
        api_dir = app_dir.joinpath("api")
        self.copy_directory(source_path=api_dir, target_path=temp_project_path)
        zip_filename = self.zip_directory(
            zip_filename="lambda.zip", file_dir=temp_project_path
        )
        return zip_filename

