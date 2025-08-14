import bcrypt
import boto3
from django.conf import settings
from applications.my_app.models import CloudAccount
import requests
from rest_framework.response import Response

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
    
def renew_gg_token(user_id):
    cloud_obj = CloudAccount.objects.filter(user__id=user_id, platform='google_drive').first()
    refresh_token = cloud_obj.credentials.get('refresh_token', None)
    
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    token_url = "https://oauth2.googleapis.com/token"
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to renew token: {response.status_code} {response.text}")
    
    print ("New token:", response.json())
    access_token = response.json().get('access_token')
    return access_token
    
def check_google_token(access_token):
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    params = {"access_token": access_token}
    r = requests.get(url, params=params)

    if r.status_code == 200:
        return True  
    else:
        return False 
    
def extract_gg_token(auth_code):
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': auth_code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': "postmessage",
        'grant_type': 'authorization_code'
    }
    token_response = requests.post(token_url, data=token_data)
    if token_response.status_code != 200:
        print("Token exchange failed:", token_response.json())
        return Response({'error': 'Failed to exchange auth code for token'}, status=400)

    token_json = token_response.json()
    access_token = token_json.get('access_token')
    refresh_token = token_json.get('refresh_token') 
    return access_token, refresh_token
    