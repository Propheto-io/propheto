import os
import pickle
import boto3
import json
from pathlib import Path
from botocore.exceptions import ClientError
from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


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


class LogsResponse(BaseModel):
    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str
    Owner: dict


class Response(BaseModel):
    code: int
    message: str
    result: bool


@router.get("/logs", summary="Get a specific log based on file key")
def get_log(log_file: str):
    response = {}
    # %{get_logs_code}%
    return response 


@router.get(
    "/logs/list", summary="List available logs"
)
def get_logs(q: Optional[str] = None):
    response = {}
    # %{list_logs_code}%
    return response


@router.post("/logs", summary="Create a new log")
async def create_log(filename: str, file_data: str):
    response = {}
    # %{create_logs_code}%
    return response


# @router.get("/logs/{run_id}", response_model=List[LogsResponse])
# def get_logs(run_id: Optional[str] = "all"):
#     s3client = boto3.client("s3")
#     delimiter = f"{run_id}*" if run_id != "all" else "*"
#     response = s3client.list_objects(Bucket="test", Delimeter=delimiter)
#     return response["Contents"]

