from django.shortcuts import render
# from rest_framework.response import Response
import requests
from rest_framework.decorators import api_view
from allauth.socialaccount.models import SocialAccount, SocialToken
from applications.my_app.serializers import RegisterSerializer, LoginSerializer, UserSerializer
from applications.my_app.models import User
from applications.commons.utils import check_password
from applications.my_app.token import AuthenticationToken
from applications.my_app.decorator import auth_required
from applications.commons.exception import APIWarningException
from applications.commons.log_lib import APIResponse, trace_api
# Create your views here.


def list_google_drive_files(request):
    try:
        # 1. Tìm Social Account của người dùng hiện tại cho provider 'google'
        social_account = SocialAccount.objects.get(user=request.user, provider='google')
        print (f"Social Account: {social_account}")
        # 2. Từ Social Account, lấy token đang hoạt động
        # Django-allauth tự động quản lý việc làm mới token khi cần
        social_token = SocialToken.objects.get(account=social_account)
        access_token = social_token.token
        refresh_token = social_token.token_secret
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': social_token.expires_at
        })
        
        
    except SocialAccount.DoesNotExist:
        # Xử lý trường hợp người dùng chưa kết nối tài khoản Google
        return render(request, 'please_connect_google.html')
    
    
# /auth/register
@api_view(['POST'])
@trace_api(class_response=APIResponse)
def api_register(request, _response: APIResponse, **kwargs):
    
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    else:
        _response.message = "Invalid data"
        return APIWarningException(f"{_response.message}")
    
    user = serializer.instance
    token = AuthenticationToken(user_id=user.id, expired_at=60*5, email=user.email).token
    
    _response.message = "User created successfully"
    _response.data_resp.update({
        'user': serializer.data, 
        'token': token
    })
    

# /auth/login
@api_view(['POST'])
@trace_api(class_response=APIResponse)
def api_login(request, _response: APIResponse, **kwargs):
    
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        _response.message = "Invalid login data"
        _response.errors = serializer.errors
        return APIWarningException(f"{_response.message}")
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = User.objects.filter(username=username).first()
    if not user:
        _response.message = "User not found"
        return APIWarningException(f"{_response.message}")
    if not check_password(password, user.password):
        _response.message = "Incorrect password"
        return APIWarningException(f"{_response.message}")
    
    token = AuthenticationToken(user_id=user.id, expired_at=60*5, email=user.email).token
    
    _response.message = "Login successful"
    _response.data_resp.update({
        'user': serializer.data,
        'token': token
    })



@api_view(['GET'])
@trace_api(class_response=APIResponse)
@auth_required()
def api_get_user_info(request, user_id, _response: APIResponse, **kwargs):
    """
    API để lấy thông tin người dùng từ token
    """
    # get from kwargs.update in auth_required decorator
    user = User.objects.filter(id=user_id).first()
    if not user:
        _response.message = "User not found"
        return APIWarningException(f"{_response.message}")
    
    user_serializer = UserSerializer(user)
    _response.data_resp={
        'user': user_serializer.data,
    }
    


