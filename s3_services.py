import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Dict


class S3Service:
    def __init__(self, config_path: str = "app-config/config.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_BUCKET", "AWS_REGION", "AWS_S3_ENDPOINT"]
        for key in required_keys:
            if key not in config or not config[key]:
                raise ValueError(f"Thiếu hoặc rỗng khóa cấu hình: {key}")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=config["AWS_SECRET_ACCESS_KEY"],
            endpoint_url=config["AWS_S3_ENDPOINT"],
            region_name=config["AWS_REGION"],
            config=Config(
                s3={'addressing_style': 'path'},  
                signature_version='s3v4'         
            )
        )
        
        self.bucket_name = config["AWS_S3_BUCKET"]
    
    async def generate_presigned_url(self, filename: str, content_type: str) -> Dict[str, str]:
        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            file_key = f"{timestamp}_{filename}"
            
            print(f"Generating presigned URL for bucket: {self.bucket_name}, key: {file_key}, content_type: {content_type}")
            
            put_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=360
            )
            
            print(f"Generated URL: {put_url}")
            return {
                "putUrl": put_url,
                "fileKey": file_key
            }
            
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    async def generate_presigned_get_url(self, key: str, expires_in_seconds: int = 604800) -> str:
        try:
            print(f"Generating presigned GET URL for bucket: {self.bucket_name}, key: {key}")
            
            get_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in_seconds
            )
            
            print(f"Generated GET URL: {get_url}")
            return get_url
            
        except ClientError as e:
            print(f"Error generating presigned GET URL: {e}")
            raise Exception(f"Error generating presigned get URL: {str(e)}")