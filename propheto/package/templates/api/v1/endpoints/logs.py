import pickle
import boto3
import json
from botocore.exceptions import ClientError
from fastapi import APIRouter
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


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
def get_log(key: str):
    s3client = boto3.client("s3")
    try:
        response = s3client.get_object(Bucket="%{bucket_name}%", Key=key)
        body = response["Body"]
        if str(key.split(".")[-1]).lower() == "json":
            return json.loads(body.read())
        else:
            return body.read()
    except ClientError as error:
        if error.response["Error"]["Code"] == "NoSuchKey":
            return f"Key not found - {key}"
        else:
            raise


@router.get(
    "/logs/list", response_model=List[LogsResponse], summary="List available logs"
)
def get_logs(q: Optional[str] = None):
    s3client = boto3.client("s3")
    delimiter = q if q else "*propheto-log-*"
    prefix = "%{project_name}%/logs"
    response = s3client.list_objects(
        Bucket="%{bucket_name}%", Prefix=prefix, Delimiter=delimiter
    )
    return response["Contents"]


@router.post("/logs", summary="Create a new log")
async def create_log(filename: str, filedata: str):
    s3client = boto3.client("s3")
    log_base = "%{project_name}%/logs"
    response = s3client.put_object(
        Body=filedata, Bucket="%{bucket_name}%", Key=f"{log_base}/{filename}"
    )
    return response


# @router.get("/logs/{run_id}", response_model=List[LogsResponse])
# def get_logs(run_id: Optional[str] = "all"):
#     s3client = boto3.client("s3")
#     delimiter = f"{run_id}*" if run_id != "all" else "*"
#     response = s3client.list_objects(Bucket="test", Delimeter=delimiter)
#     return response["Contents"]

