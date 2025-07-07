import datetime
import jwt
from django.conf import settings
import os
from Crypto.Cipher import AES
from base64 import b64encode,b64decode
import json
from Crypto.Util.Padding import pad,unpad

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


class AESCipher:
    def __init__(self, key: bytes):
        self.key = key

    
    def encrypt(self, data: bytes) -> str:
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data, AES.block_size))
        iv = b64encode(cipher.iv).decode('utf-8')
        ct = b64encode(ct_bytes).decode('utf-8')
        result = json.dumps({'iv':iv, 'ciphertext':ct})
        # print(result)
        return result
    
    def decrypt(self, encrypted_data):
        try:
            b64 = json.loads(encrypted_data)
            iv = b64decode(b64['iv'])
            ct = b64decode(b64['ciphertext'])
            cipher = AES.new(self.key, AES.MODE_CBC, iv) 
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            # print("The message was: ", pt)
        except (ValueError, KeyError):
            print("Incorrect decryption")
        
        return pt