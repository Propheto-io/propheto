import os
import pickle
from datetime import datetime
from time import time
from typing import Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

## ---- PYTORCH ----
DESERIALIZE_PYTORCH = """
    # DESERIALIZE PYTORCH
    import torch
    import cloudpickle

    s3client = boto3.client("s3")
    response = s3client.get_object(Bucket="%{bucket_name}%", Key="%{object_key}%")
    body = response["Body"].read()
    
    model = cloudpickle.loads(body)
"""

PREPROCESS_PYTORCH = """
    import torch
    data = float(data)
    data = torch.tensor([[data]])
"""

PREDICT_PYTORCH = """
    pred = model(data) 
"""

POSTPROCESS_PYTORCH = """
    pred = [float(pred)]
"""

### ---- SKLEARN ----

DESERIALIZE_SKLEARN = """
    # DESERIALIZE SKLEARN
    import sklearn
    import pickle

    s3client = boto3.client("s3")
    response = s3client.get_object(Bucket="%{bucket_name}%", Key="%{object_key}%")
    body = response["Body"].read()

    model = pickle.loads(body)
    print(model)
"""

PREPROCESS_SKLEARN = """
    # data = float(data)
    # data = [[data]]
"""

PREDICT_SKLEARN = """
    pred = model.predict(data) 
"""

POSTPROCESS_SKLEARN = """
    pred = pred.tolist()[0]
"""

## ---- TENSORFLOW ----

DESERIALIZE_TENSORFLOW = """
    # DESERIALIZE TENSORFLOW
    import tempfile
    from tensorflow.keras.models import load_model

    s3client = boto3.client("s3")
    with tempfile.TemporaryDirectory() as tempdir:
        filename = f"{tempdir}/model.h5"
        result = s3client.download_file(Bucket="%{bucket_name}%", Key="%{object_key}%", Filename=filename)
        model = load_model(filename)
        print(model)
"""

PREPROCESS_TENSORFLOW = """
    data = float(data)
    data = [[data]]
"""

PREDICT_TENSORFLOW = """
    pred = model.predict(data) 
"""

POSTPROCESS_TENSORFLOW = """
    pred = float(pred[0][0])
"""

## ---- XGBOOST ----
DESERIALIZE_XGBOOST = """
    # DESERIALIZE PYTORCH
    import xgboost
    import cloudpickle

    s3client = boto3.client("s3")
    response = s3client.get_object(Bucket="%{bucket_name}%", Key="%{object_key}%")
    body = response["Body"].read()
    
    model = cloudpickle.loads(body)
"""

PREPROCESS_XGBOOST = """
    import numpy as np
    data = float(data)
    data = np.array([[data]])
"""

PREDICT_XGBOOST = """
    pred = model.predict(data)
"""

POSTPROCESS_XGBOOST = """
    pred = [float(pred)]
"""


class ModelSerializer:
    """
    Class to serialize and deserialize model objects based on the ML package type.
    """

    # TODO: REFACTOR FOR INDIVIDUAL ML PACKAGES

    def __init__(
        self,
        model_type: str = "sklearn",
        file_path: str = "",
        created_at: datetime = datetime.fromtimestamp(time()),
        *args,
        **kwargs,
    ) -> None:
        self.model_type = model_type
        self.file_path = file_path
        self.created_at = created_at

    def _get_model_type(self, model: object) -> str:
        """
        Determine what ML library the model was built using
        """
        model_type = None
        # SCIKIT LEARN
        try:
            import sklearn

            is_sklearn = isinstance(model, sklearn.base.BaseEstimator)
            if is_sklearn:
                model_type = "sklearn"
        except ImportError:  # module not found
            pass

        # PYTORCH
        try:
            import torch

            is_pytorch = isinstance(model, torch.nn.modules.module.Module)
            if is_pytorch:
                model_type = "pytorch"
        except ImportError:  # module not found
            pass

        # TENSORFLOW
        try:
            import tensorflow as tf

            is_tensorflow = isinstance(model, tf.keras.models.Sequential)
            if is_tensorflow:
                model_type = "tensorflow"
        except ImportError:  # module not found
            pass

        # XGBOOST
        try:
            import xgboost as xgb

            is_xgboost = isinstance(model, xgb.XGBModel)
            if is_xgboost:
                model_type = "xgboost"
        except ImportError:  # module not found
            pass

        return model_type

    def _save_sklearn(self, model: object, save_path: str):
        """
        Save the Scikit-learn model object to a local file
        """
        try:
            pickle.dump(model, open(Path(save_path , "model.sav"), "wb"))
            self.file_path = Path(save_path , "model.sav")
            self.model_name = "model.sav"
            # print(self.file_path)
        except:
            pass

    def _load_sklearn(self, model_path: str) -> object:
        """
        Load Scikit Learn model and return model object.
        """
        try:
            # load the model from disk
            with open(model_path, "rb") as model_file:
                model = pickle.load(model_file)
        except ImportError:  # module not found
            pass
        return model

    def _save_pytorch(self, model: object, save_path: str):
        try:
            import torch
            import cloudpickle

            file_path_dst = Path(save_path , "model.pth")
            cloudpickle.dump(model, open(file_path_dst, "wb"))
            self.file_path = file_path_dst
        except ImportError:  # module not found
            pass

    def _load_pytorch(self, model_path: str) -> object:
        model = object
        try:
            import cloudpickle

            model = cloudpickle.load(open(model_path, "rb"))
        except ImportError:  # module not found
            pass
        return model

    def _save_tensorflow(self, model: object, save_path: str) -> str:
        # TODO: IMPROVE THE TYPES FOR THE MODELS PER PACKAGE
        try:
            import tensorflow as tf

            # Save the entire model to a HDF5 file.
            # The '.h5' extension indicates that the model should be saved to HDF5.
            model.save(Path(save_path , "model.h5"))
            self.file_path = Path(save_path , "model.h5")
        except ImportError:  # module not found
            pass
        return Path(save_path , "model.h5")

    def _load_tensorflow(self, model_path: str) -> object:
        model = object
        try:
            # https://stackoverflow.com/questions/47847942/load-keras-model-with-aws-lambda
            import tensorflow as tf

            model = tf.keras.models.load_model(model_path)
        except ImportError:  # module not found
            pass
        return model

    def _save_xgboost(self, model: object, save_path: str) -> str:
        # Can use model.save_model('model_file_name.json') but deserializing is weird.
        # going to use pickle
        try:
            import xgboost
            import cloudpickle

            file_path_dst = Path(save_path , "model.pkl")
            cloudpickle.dump(model, open(file_path_dst, "wb"))
            self.file_path = file_path_dst
        except ImportError:  # module not found
            pass

    def _load_xgboost(self, model_path: str) -> object:
        # bst = xgboost.Booster
        # bst.load_model('model_file_name.json')
        model = object
        try:
            import cloudpickle

            model = cloudpickle.load(open(model_path, "rb"))
        except ImportError:  # module not found
            pass
        return model

    def get_model_processing_code(self, model_type: str = None) -> Tuple[str]:
        """
        Serialize the model to local directory based on the model type.

        Parameters
        ----------
        model_type : str
                String representing the type of model
        
        Returns
        -------
        serialization_code : str
                String containing the specific serialization code
        """
        model_type = model_type if model_type else self.model_type
        serialization_code = (
            preprocessing_code
        ) = predict_code = postprocessing_code = ""
        if model_type == "sklearn":
            serialization_code = DESERIALIZE_SKLEARN
            preprocessing_code = PREPROCESS_SKLEARN
            predict_code = PREDICT_SKLEARN
            postprocessing_code = POSTPROCESS_SKLEARN
        elif model_type == "pytorch":
            serialization_code = DESERIALIZE_PYTORCH
            preprocessing_code = PREPROCESS_PYTORCH
            predict_code = PREDICT_PYTORCH
            postprocessing_code = POSTPROCESS_PYTORCH
        elif model_type == "tensorflow":
            serialization_code = DESERIALIZE_TENSORFLOW
            preprocessing_code = PREPROCESS_TENSORFLOW
            predict_code = PREDICT_TENSORFLOW
            postprocessing_code = POSTPROCESS_TENSORFLOW
        elif model_type == "xgboost":
            serialization_code = DESERIALIZE_XGBOOST
            preprocessing_code = PREPROCESS_XGBOOST
            predict_code = PREDICT_XGBOOST
            postprocessing_code = POSTPROCESS_XGBOOST
        else:
            raise Exception(f"INVALIDE MODEL TYPE {model_type}")
        return serialization_code, preprocessing_code, predict_code, postprocessing_code

    def save_model(self, model: object, save_path: str = "", *args, **kwargs) -> str:
        """
        Serialize the model to local directory based on the model type.

        Parameters
        ----------
        model : object
                Trained model object from base ML library
        save_path : str, optional
                Path for the output of the saved model. If not passed default to current directory.
        model_class_str : str, optional
                Class definition for the model object. required for pytorch models only.
        """
        model_type = self._get_model_type(model)
        self.model_type = model_type
        save_path = save_path if save_path != "" else os.getcwd()
        self.save_path = save_path
        if model_type == "sklearn":
            self._save_sklearn(model, save_path)
        elif model_type == "tensorflow":
            self._save_tensorflow(model, save_path)
        elif model_type == "pytorch":
            self._save_pytorch(model, save_path)
        elif model_type == "xgboost":
            self._save_xgboost(model, save_path)
        else:
            raise Exception("Model type error. Please check that the model is correct")
        return save_path


