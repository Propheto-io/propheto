import boto3
from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class Response(BaseModel):
    code: int
    message: str
    result: bool


@router.get("/alerts/{run_id}")
def get_alerts(run_id: str):
    s3client = boto3.client("s3")
    # Delimiter = model_name  #TODO: Figure out the model name param delimeter
    response = s3client.list_objects(Bucket="test")
    return response["Contents"]
