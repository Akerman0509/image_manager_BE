

from applications.commons.exception import APIWarningException
from applications.commons.log_lib import APIResponse
from applications.my_app.token import AuthenticationToken


def auth_required():
    def decorator(func):
        def inner(**kwargs):
            request = kwargs.get('request')
            _response = kwargs.get('response', APIResponse())
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                print ("❗ Authorization header missing")
                _response.message = "Authorization header missing"
                _response.code_status = 1401
                raise APIWarningException(_response.message)
            
            auth_type, access_token = auth_header.split(" ")
            access_token = access_token.strip('"') # python, really???
            if auth_type.lower() != 'bearer':
                _response.message = "Invalid authorization type, NOT Bearer"
                _response.code_status = 1401
                raise APIWarningException(_response.message)

            if not access_token:
                _response.message = "Token is missing"
                _response.code_status = 1401
                raise APIWarningException(_response.message)
            
            if AuthenticationToken.is_token_expired(AuthenticationToken.auth(access_token)):
                _response.message = "Token is expired"
                _response.code_status = 1401
                raise APIWarningException(_response.message)
            
            token = AuthenticationToken.auth(access_token)
            if not token:
                _response.message = "Unauthorized"
                _response.code_status = 1401
                raise APIWarningException(_response.message)
            
            kwargs.update(token=token)
            return func(**kwargs)
        
        return inner
    
    return decorator



