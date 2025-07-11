from django.shortcuts import render
# from rest_framework.response import Response
import requests
from rest_framework.decorators import api_view
from applications.my_app.serializers import RegisterSerializer, LoginSerializer, UserSerializer, FolderSerializer
from applications.my_app.models import User,DriveAccount, Image, Folder
from applications.commons.utils import check_password
from applications.my_app.token import AuthenticationToken
from applications.my_app.decorator import auth_required
from applications.commons.exception import APIWarningException
from applications.commons.log_lib import APIResponse, trace_api
from rest_framework.response import Response
from django.core.files.base import ContentFile


from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.views.decorators.csrf import csrf_exempt

# Create your views here.


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:3000/callback' # Your frontend callback URL
    client_class = OAuth2Client

    
# /auth/register
@api_view(['POST'])
def api_register(request):
    
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    else:
        return Response(serializer.errors, status=400)
    
    user = serializer.instance
    token = AuthenticationToken(user_id=user.id, expired_at=60*5, email=user.email).token
    
    return Response({
        'user': serializer.data,
        'token': token
    }, status=201)


# /auth/login
@api_view(['POST'])
def api_login(request):
    
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        print ("Login serializer is not valid:", serializer.errors)
        return Response(serializer.errors, status=400)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    user = User.objects.filter(email=email).first()
    if not user:
        print ("User not found with username:", email)
        return Response({'error': 'User not found'}, status=404)
    if not check_password(password, user.password):
        print ("Password is incorrect for user:", email)
        return Response({'error': 'Incorrect password'}, status=401)
    
    token = AuthenticationToken(user_id=user.id, expired_at=60*5, email=user.email).token
    
    print ("Login successful for user:", email)
    
    user_serializer = UserSerializer(user)
    user_info = user_serializer.data
    
    return Response({
        'user': user_info,
        'token': token
    }, status=200)



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
    
@csrf_exempt
@api_view(['POST'])
def api_create_folder(request):
    print ("Creating folder with data:", request.data)
    serializer = FolderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    else:
        return Response(serializer.errors, status=400)
    
    
    
    
@api_view(['POST'])
def api_save_drive_token(request):
    """
    API để lưu token Google Drive
    """
    
    print ("Saving Google Drive token with data:", request.data)
    try :
        token = request.data.get('access_token')
        email = request.data.get('drive_email')
        user_id = request.data.get('user_id')
        
        user = User.objects.filter(id=user_id).first()
        
        
        drive_account = DriveAccount.objects.filter(user=user).first()
        if not drive_account:
            print ("Creating new DriveAccount for user:", user.username)
            drive_account = DriveAccount.objects.create(
                user=user,
                drive_email=email,
                access_token=token
                )
        else: 
            print ("Updating existing DriveAccount for user:", user.username)
            drive_account.access_token = token
            drive_account.save()
        
        print ("Token saved successfully for user:", user.username)
    except Exception as e:
        print ("Error saving token:", str(e))
        return Response({'error': 'Failed to save token'}, status=500)
    
    return Response({'message': 'Token saved successfully'}, status=200)


@api_view(['POST'])
def api_sync_img(request):
    """
    API để lưu ảnh lên server
    """
    try:
        user_id = request.data.get('user_id')
        drive_email = request.data.get('drive_email')
        img_name = request.data.get('img_name')
        img_id = request.data.get('img_id')
        img_folder_id = request.data.get('img_folder_id')
        
        user = User.objects.filter(id=user_id).first()
        folder = Folder.objects.filter(id=img_folder_id).first()
        drive_account = DriveAccount.objects.filter(user=user, drive_email=drive_email).first()

        access_token = drive_account.access_token
        
        print (f"user: {user.username}, drive_email: {drive_email}, img_name: {img_name}, img_id: {img_id}, img_folder_id: {img_folder_id}, access_token: {access_token}")

        # Get image content from Google Drive
        drive_url = f"https://www.googleapis.com/drive/v3/files/{img_id}?alt=media"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(drive_url, headers=headers)

        if response.status_code != 200:
            return Response({"error": "Failed to download image from Google Drive"}, status=500)

        # Save image to Django model
        img_content = ContentFile(response.content)
        img_model = Image(
            user=user,
            image_name=img_name,
            folder=folder
        )
        img_model.image.save(img_name, img_content)
        img_model.save()
        
    except Exception as e:
        print("Error saving image:", str(e))
        return Response({"error": "Failed to save image"}, status=500)

    return Response({"message": "Image saved successfully", "image_id": img_model.id})


    
@api_view(['POST'])
def api_upload_img(request):
    """
    API để upload ảnh lên server
    """
    try:
        user_id = request.data.get('user_id')
        folder_id = request.data.get('folder_id')
        img_file = request.FILES.get('img_file')
        image_name = img_file.name
        user = User.objects.filter(id=user_id).first()
        folder = Folder.objects.filter(id=folder_id).first()
        
        if not user or not folder:
            return Response({"error": "User or folder not found"}, status=404)
        
        img_model = Image(
            user=user,
            image=img_file,
            folder=folder,
            image_name=image_name
        )
        img_model.save()
        
    except Exception as e:
        print("Error uploading image:", str(e))
        return Response({"error": "Failed to upload image"}, status=500)

    return Response({"message": "Image uploaded successfully", "image_id": img_model.id})




@api_view(['GET'])
def api_get_images(request, user_id, folder_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)
    
    folder = Folder.objects.filter(id=folder_id, owner=user).first()
    if not folder:
        return Response({"error": "Folder not found"}, status=404)
    
    images = Image.objects.filter(folder=folder).values('id', 'image_name', 'image', 'created_at')
    
    return Response({"images": list(images)}, status=200)