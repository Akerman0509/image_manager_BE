import datetime
import jwt
from django.conf import settings
import os

class AuthenticationToken(object):
    def __init__(self, user_id:str , expired_at: int, email:str):
        self.sub = str(user_id)
        self.expired_at = datetime.datetime.now() + datetime.timedelta(seconds=expired_at)
        self.email = email
        
    @property
    def token(self):
        payload = {
            "sub": self.sub,
            "exp": int(self.expired_at.timestamp()),
            "email": self.email   
        }
        private_key_path = os.path.join(settings.BASE_DIR, 'private_key.pem')
        with open(private_key_path, "r") as f:
            private_key = f.read()

        token = jwt.encode(payload, private_key, algorithm='RS256')
        return token
    
    @classmethod
    def auth(cls, token):
        ins = None
        try:
            key_path = os.path.join(settings.BASE_DIR, 'public_key.pem')
            with open(key_path, 'r') as f:
                public_key = f.read()

            # Decode and verify the token using the public key and RS256 algorithm
            payload = jwt.decode(token, public_key, algorithms=['RS256'])
            
            ins = cls(
                user_id=payload.get("sub"),
                expired_at=payload.get("exp") - int(datetime.datetime.now().timestamp()),
                email=payload.get("email")
            )
            
        except Exception as e:
            print(f"Token decode error: {e}")
        return ins
        
        
    @staticmethod
    def is_token_expired(token):
        current_time = datetime.datetime.now()
        return current_time > token.expired_at
