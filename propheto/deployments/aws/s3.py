import os
import requests
from tqdm import tqdm
from ...utilities import human_size, unique_id, get_list_directory_files
from .boto_session import BotoInterface
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class S3(BotoInterface):
    """
    Manage objects in S3
    """

    def __init__(
        self,
        profile_name: Optional[str] = "default",
        s3_bucket_name: Optional[str] = "",
        region: Optional[str] = "us-east-1",
        *args,
        **kwargs,
    ) -> None:
        super().__init__(profile_name=profile_name, region=region)
        self.s3_client = self.boto_client.client("s3")
        self.s3_bucket_name = s3_bucket_name
        self.profile_name = profile_name
        self.region = region

    def to_dict(self) -> dict:
        """
        Method to convert class instance to dictionary
        """
        output_dict = {}
        output_dict["profile_name"] = self.profile_name
        output_dict["s3_bucket_name"] = self.s3_bucket_name
        return output_dict

    def __repr__(self) -> str:
        if self.s3_bucket_name != "":
            return f"S3(profile_name={self.profile_name}, s3_bucket_name={self.s3_bucket_name})"
        else:
            return f"S3(profile_name={self.profile_name})"

    def __str__(self) -> str:
        if self.s3_bucket_name != "":
            return f"S3(profile_name={self.profile_name}, s3_bucket_name={self.s3_bucket_name})"
        else:
            return f"S3(profile_name={self.profile_name})"

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ["boto_client", "s3_client"]:
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
        self.s3_client = self.boto_client.client("s3")

    def manage_bucket(self) -> None:
        pass

    def upload_folder(
        self, project_name: str, local_folder_path: str, output_folder_path: str
    ) -> str:
        """
        Upload a folder and all of the contents into a given s3 bucket.

        Parameters
        ----------
        project_name : str
                Project name within the bucket 
        local_folder_path : str 
                Path to the local folder to upload into S3
        output_folder_path : str
                Output folder

        Returns
        -------
        s3_key : str
                S3 key string
        """
        local_files = get_list_directory_files(local_folder_path)
        for _local_file in local_files:
            filename = _local_file.parts[-1]
            self.upload_file(
                filename=filename,
                project_name=Path(project_name, output_folder_path),
                # project_name=project_name,
                source_path=_local_file,
            )
        s3_key = f"{self.s3_bucket_name}/{project_name}/{output_folder_path}"
        return s3_key

    def create_bucket(self, bucket_name: str, tags: dict = None) -> str:
        """
        Create a new bucket in S3
        
        Parameters
        ----------
        bucket_name : str,
                The required new bucket name to create
        tags : dict, optional
                Dictionary of tags to use 
        """
        # strange behavior with us-east-1 being default region.
        # dont specify if so
        bucket_name = bucket_name.replace(" ", "")
        for number in range(10):
            bucket_name = bucket_name.replace(str(number), "")
        bucket_name += "-" + unique_id(length=6, has_numbers=False)
        bucket_name = bucket_name.lower()
        self.s3_bucket_name = bucket_name
        if self.region == "us-east-1":
            BucketResponse = self.s3_client.create_bucket(Bucket=self.s3_bucket_name,)
        else:
            BucketResponse = self.s3_client.create_bucket(
                Bucket=self.s3_bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region},
            )
        if tags:
            tags = {
                "TagSet": [{"Key": key, "Value": self.tags[key]} for key in tags.keys()]
            }
            self.s3_client.put_bucket_tagging(Bucket=self.s3_bucket_name, Tagging=tags)
        return bucket_name

    def delete_object(self, bucket_name: str, object_key: str) -> dict:
        """
        Delete an S3 Object

        Parameters
        ----------
        bucket_name : str
                The AWS S3 BucketName that is to be deleted
        object_key : str
                The key for the object to be deleted
        """
        response = self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return response

    def empty_bucket(self, bucket_name: str) -> dict:
        """
        Empty the s3 Bucket of all contents.

        Parameters
        ----------
        bucket_name : str
                The AWS S3 BucketName that is to be emptied
        """
        list_response = self.s3_client.list_objects(Bucket=bucket_name)
        delete_objects_response = {}
        if "Contents" in list_response:
            bucket_contents = list_response["Contents"]
            bucket_objects = [{"Key": record["Key"]} for record in bucket_contents]
            delete_objects_response = self.s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": bucket_objects, "Quiet": False},
            )
        return delete_objects_response

    def destroy(self, bucket_name: str) -> dict:
        """
        Destroy the given S3 bucket. First need to empty it of contents then delete the bucket

        Parameters
        ----------
        bucket_name : str
                S3 Bucket name which will be destroyed
        Returns
        -------
        delete_bucket_response : dict
                Response object from s3 client delete bucket command
        """
        delete_objects_response = self.empty_bucket(bucket_name)
        delete_bucket_response = self.s3_client.delete_bucket(Bucket=bucket_name)
        return delete_bucket_response

    def upload_file(
        self, filename: str, project_name: str, source_path: Optional[str] = ""
    ) -> str:
        """
        Upload given file to S3 bucket

        Parameters
        ----------
        filename : str
                File that will be uploaded
        project_name : str
                Name of the current ML project/service 
        source_path : str, optional
                Source path for the given file. Defaults to current directory

        Returns
        -------
        dest_path : str
                S3 Path for the uploaded file/folder 

        """
        source_path = source_path if source_path != "" else Path(os.getcwd(), filename)
        dest_path = str(Path(str(project_name), str(filename)))
        source_size = os.stat(source_path).st_size
        print("Uploading {0} ({1})..".format(dest_path, human_size(source_size)))
        progress = tqdm(
            total=float(os.path.getsize(source_path)), unit_scale=True, unit="B"
        )
        self.s3_client.upload_file(
            str(source_path),
            str(self.s3_bucket_name),
            str(dest_path),
            Callback=progress.update,
        )
        progress.close()
        return dest_path

