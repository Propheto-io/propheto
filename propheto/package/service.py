import os
import errno
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PKG_DIRECTORY_PATH = str(Path(os.path.abspath(__file__)).parent.absolute())
API_TEMPLATES_DIRECTORY = Path(PKG_DIRECTORY_PATH, "templates", "api")


def get_list_directory_files(directory_path: str) -> list:
    """
    Utility function for getting the directory files.
    """
    directory_contents = os.listdir(directory_path)
    directory_files = []
    for _item in directory_contents:
        _path = Path(directory_path, _item)
        if os.path.isdir(_path):
            subdirectory_files = get_list_directory_files(_path)
            directory_files.extend(subdirectory_files)
        else:
            # Exclude any cache files
            if str(_path)[-4:] != ".pyc": 
                directory_files.append(_path)
    return directory_files


class APIService:
    """
    Create the API code for the client environment.
    """

    def __init__(self, *args, **kwargs) -> None:
        self.bucket = ""

    def _generate_file(self, filename: str, file_contents: str) -> None:
        # Making directorys as well as files so need to create those
        if not os.path.exists(os.path.dirname(filename)):
            try:
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(filename, "w") as output_file:
            output_file.write(file_contents)

    def _read_file(self, filename: str) -> str:
        with open(filename, "r") as _file:
            file_data_str = _file.read()
        return file_data_str

    @staticmethod
    def get_list_api_template_files() -> list:
        """
        Get a list of all the API template files.
        """
        # GET ALL THE API TEMPLATE FLIES
        template_files = get_list_directory_files(API_TEMPLATES_DIRECTORY)
        return template_files

    def generate_service(
        self,
        model_serializer: str,
        model_preprocessor: str,
        model_predictor: str,
        model_postprocessor: str,
        project_name: str,
        list_model_code: str,
        list_logs_code: str,
        get_logs_code: str,
        create_logs_code: str,
        bucket_name: Optional[str] = "",
        object_key: Optional[str] = "",
        model_filepath: Optional[str] = "",
        logs_path: Optional[str] = "",
        output_path: Optional[str] = "",
        api_root_path: Optional[str] = "openapi_prefix",
        *args,
        **kwargs,
    ) -> str:

        """
        Generate an API service for the ML project.

        Parameters
        ----------
        model_serializer : str
                Model serialzier code
        model_preprocessor : str
                Data preprocessor and transformation for the model
        model_predictor : str
                Predictor code for the actual model predictions 
        model_postprocessor : str
                Prostprocessing and data transformation code for the predictions before returning
        project_name : str
                Project name created from the S3 Bucket
        list_model_code: str
                API code for listing models from remote model registry
        list_logs_code: str
                API code for listing log files from remote log storate
        get_logs_code: str
                API code for getting logs from remote log DB
        create_logs_code: str
                Cod to create new logfile
        bucket_name : str, optional
                Bucket name for the model artifacts.
        object_key : str, optional
                Specific object key for the model file.        
        model_filepath : str, optional
                Path to the stored model file
        logs_path : str, optional
                Filepath to the logfiles
        output_path : str, optional
                Output path directory for the API codes
        api_root_path : str, optional
                'root_path' argument for API prefix.
        Returns
        -------
        base_dir : str
            Output path for the generated API service code
        """
        output_path = output_path if output_path != "" else os.getcwd()
        base_dir = Path(output_path, "api")
        DIR_PATH = Path(base_dir)
        DIR_PATH.mkdir(parents=True, exist_ok=True)
        # os.mkdir(f"{base_dir}")
        template_files = self.get_list_api_template_files()
        for filename in template_files:
            file_contents = self._read_file(filename)
            file_contents = file_contents.replace("%{model_serializer}%", model_serializer)
            file_contents = file_contents.replace("%{model_preprocessor}%", model_preprocessor)
            file_contents = file_contents.replace("%{model_predictor}%", model_predictor)
            file_contents = file_contents.replace("%{model_postprocessor}%", model_postprocessor)

            file_contents = file_contents.replace("%{list_model_code}%", list_model_code)
            file_contents = file_contents.replace("%{list_logs_code}%", list_logs_code)
            file_contents = file_contents.replace("%{get_logs_code}%", get_logs_code)
            file_contents = file_contents.replace("%{create_logs_code}%", create_logs_code)

            file_contents = file_contents.replace("%{logs_path}%", logs_path)

            file_contents = file_contents.replace("%{bucket_name}%", bucket_name)
            file_contents = file_contents.replace("%{project_name}%", project_name)
            file_contents = file_contents.replace("%{object_key}%", object_key)
            file_contents = file_contents.replace("%{model_filepath}%", model_filepath)

            file_contents = file_contents.replace("%{api_root_path}%", api_root_path)
            
            # TODO FIX THIS FILE NAMING THING AND FIGURE OUT DIRECTORY STUFF
            _filepath_parts = Path(filename).parts
            api_file_loc = -1
            for index, val in enumerate(_filepath_parts):
                if val == "api":
                    api_file_loc = index
            _output_tuple = _filepath_parts[api_file_loc + 1:]
            _output_filename = Path(*_output_tuple)
            _output_file = Path(base_dir, _output_filename)
            self._generate_file(_output_file, file_contents)
        return base_dir
