

from applications.my_app.token import AuthenticationToken

from functools import wraps
from rest_framework.response import Response

def require_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith("Bearer "):
            return Response({'error': 'Missing or invalid Authorization header'}, status=401)
        
        token = auth_header.split("Bearer ")[1]
        auth_user = AuthenticationToken.auth(token)
        if not auth_user:
            return Response({'error': 'Invalid or expired token'}, status=401)

        # Inject auth_user into request
        request.auth_user = auth_user
        return view_func(request, *args, **kwargs)

    return _wrapped_view


