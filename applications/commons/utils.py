import bcrypt
import boto3
from django.conf import settings


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # store as string in DB

def check_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if the provided plain password matches the hashed password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))




def get_miniIO_client():
    
    return boto3.client(
        's3',
        aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url= settings.AWS_S3_ENDPOINT,
        region_name= settings.AWS_REGION
    )