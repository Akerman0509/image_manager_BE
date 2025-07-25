from django.shortcuts import render
# from rest_framework.response import Response
import requests
from rest_framework.decorators import api_view
from applications.my_app.serializers import RegisterSerializer, LoginSerializer, UserSerializer, FolderSerializer
from applications.my_app.models import User, CloudAccount, Image, Folder, FolderPermission
from applications.commons.utils import check_password
from applications.my_app.token import AuthenticationToken
from applications.commons.exception import APIWarningException
from applications.commons.log_lib import APIResponse, trace_api
from rest_framework.response import Response
from django.core.files.base import ContentFile
from django.conf import settings
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json
from applications.my_app.decorator import require_auth

from applications.my_app.tasks import sync_drive_folder_task,sync_image_task
from celery.result import AsyncResult
# Create your views here.


# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = 'http://localhost:3000/callback' # Your frontend callback URL
#     client_class = OAuth2Client

    
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
    
    #check if user has gg account associated with this email
    if user.account_type == User.AccountType.GG_AUTH:
        return Response({'INFO': 'user already has gg account associated with this email, pls login with gg'}, status=400)
    
    if not check_password(password, user.password):
        print ("Password is incorrect for user:", email)
        return Response({'error': 'Incorrect password'}, status=401)
    
    token = AuthenticationToken(user_id=user.id, expired_at=60*20, email=user.email).token
    
    print ("Login successful for user:", email)
    
    user_serializer = UserSerializer(user)
    user_info = user_serializer.data
    
    return Response({
        'user': user_info,
        'token': token
    }, status=200)


@api_view(['POST'])
def api_login_with_gg(request):
    access_token = request.data.get('access_token')
    print ("[api_login_with_gg] Access token received:", access_token)
    if not access_token:
        return Response({'error': 'Access token is required'}, status=400)

    # Step 1: Verify with Google
    headers = {"Authorization": f"Bearer {access_token}"}
    google_response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)

    if google_response.status_code != 200:
        print ("Google response error:", google_response.json())
        return Response({'error': 'Invalid Google access token'}, status=400)

    google_data = google_response.json()
    email = google_data.get('email')
    username = google_data.get('name') or email.split('@')[0]

    if not email:
        return Response({'error': 'Email not found in Google data'}, status=400)
    
    # check if user exists
    user = User.objects.filter(email=email).first()
    if not user:
        # Create new user if not exists
        user = User.objects.create_gg_user(
            username=username,
            email=email
        )
        print ("[api_login_with_gg] New user created:", user.username)
    token = AuthenticationToken(user_id=user.id, expired_at=60*20, email=user.email).token
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        },
        'token': token
    }, status=200)
    
    


@api_view(['GET'])
@require_auth
def api_get_user_info(request, user_id):
    """
    API để lấy thông tin người dùng từ token
    """
    # get from kwargs.update in auth_required decorator
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({'error': 'User not found'}, status=404)
    
    user_serializer = UserSerializer(user)
    return Response(user_serializer.data, status=200)
    
@api_view(['POST'])
def api_create_folder(request, user_id):
    print ("Creating folder with data:", request.data)
    data = {
        'name': request.data.get('name'),
        'owner': user_id,
    }
    serializer = FolderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    else:
        return Response(serializer.errors, status=400)
    
    
    
    
@api_view(['POST'])
@require_auth
def api_save_drive_token(request, user_id):
    """
    API để lưu token Google Drive
    """
    
    print ("Saving Google Drive token with data:", request.data)
    try :
        token = request.data.get('access_token')
        email = request.data.get('drive_email')
        refresh_token = request.data.get('refresh_token')
        
        user = User.objects.filter(id=user_id).first()
        
        
        drive_account = CloudAccount.objects.filter(user=user).first()
        credentials = {
            "access_token": token,
            "refresh_token":refresh_token
        }
        
        if not drive_account:
            print ("Creating new DriveAccount for user:", user.username)
            drive_account = CloudAccount.objects.create(
                user=user,
                drive_email=email,
                credentials = credentials
                )
        else: 
            print ("Updating existing DriveAccount for user:", user.username)
            drive_account.credentials = credentials
            drive_account.save()
        
        print ("Token saved successfully for user:", user.username)
    except Exception as e:
        print ("Error saving token:", str(e))
        return Response({'error': 'Failed to save token'}, status=500)
    
    return Response({'message': 'Token saved successfully'}, status=200)


@api_view(['POST'])
@require_auth
def api_sync_img(request, user_id):
    """
    API to trigger Celery task for syncing an image from Google Drive
    """
    drive_email = request.data.get('drive_email')
    img_name = request.data.get('img_name')
    img_id = request.data.get('img_id')
    img_folder_id = request.data.get('img_folder_id')

    # Trigger Celery task
    task = sync_image_task.delay(user_id, drive_email, img_name, img_id, img_folder_id)

    return Response({
        "message": "Image sync task started",
        "task_id": task.id
    })



    
@api_view(['POST'])
@require_auth
def api_upload_image(request, user_id):
    """
    API để upload ảnh lên server
    """
    try:
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


@api_view(['DELETE'])
@require_auth
def api_delete_image(request, user_id, image_id):
    """
    API để xóa ảnh
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    image = Image.objects.filter(id=image_id, user=user).first()
    if not image:
        return Response({"error": "Image not found"}, status=404)

    # Delete the image file from storage
    if image.image:
        image.image.delete(save=False)
    
    # Delete the image record from the database
    image.delete()

    return Response({"message": "Image deleted successfully"}, status=200)

@api_view(['GET'])
@require_auth
def api_get_images(request, user_id, folder_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    folder = Folder.objects.filter(id=folder_id, owner=user).first()
    if not folder:
        return Response({"error": "Folder not found"}, status=404)

    images = Image.objects.filter(folder=folder)

    image_list = []
    for img in images:
        image_list.append({
            'id': img.id,
            'image_name': img.image_name,
            'image': request.build_absolute_uri(img.image.url),
            'created_at': img.created_at,
        })

    return Response({"images": image_list}, status=200)


# {
#     "allow_read": [],
#     "allow_write": [],
#     "allow_delete": [],
# }
@api_view(['POST'])
@require_auth
def api_change_folder_permission(request, user_id, folder_id):
    
    # check if folder exists
    folder = Folder.objects.filter(id=folder_id).first()
    if not folder:
        return Response({"error": "Folder not found"}, status=404)
    # check if user exists and is owner of folder
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)
    if folder.owner != user:
        return Response({"error": "User is not the owner of the folder"}, status=403)
    
    folder_permission= FolderPermission.objects.get(folder=folder.id)
    print("Folder permission:", folder_permission)
    
    # take out list
    print (request.data)
    
    allow_read_email = request.data.get('allow_read', [])
    allow_write_email = request.data.get('allow_write', [])
    allow_delete_email = request.data.get('allow_delete', [])
    
    res = {
        "message": "Folder permissions updated successfully",
        "folder_id": folder.id
    }
    
    # append owner to all permissions
    allow_read_email.append(user.email)
    allow_write_email.append(user.email)
    allow_delete_email.append(user.email)
    
    allow_read_users = User.objects.filter(email__in=allow_read_email)
    allow_write_users = User.objects.filter(email__in=allow_write_email)
    allow_delete_users = User.objects.filter(email__in=allow_delete_email)
    folder_permission.allow_read.set(allow_read_users)  
    folder_permission.allow_write.set(allow_write_users)
    folder_permission.allow_delete.set(allow_delete_users)

    
    folder_permission.save()

    return Response(res, status=200)

@api_view(['GET'])
@require_auth
def api_home_page(request, user_id):
    """
    API để trả về trang chủ
    """
    print ("Getting home page for user:", user_id)
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)
    
    folders = Folder.objects.filter(owner=user)
    # take out folder id and folder_name
    folder_dicts = [{'id': folder.id, 'name': folder.name} for folder in folders]
    
    images = Image.objects.filter(folder__isnull=True)

    image_list = []
    for img in images:
        image_list.append({
            'id': img.id,
            'image_name': img.image_name,
            'image': request.build_absolute_uri(img.image.url),
            'created_at': img.created_at,
        })
    res = {
        'user_id': user_id,
        'folders': folder_dicts,
        'images': image_list,
    }
    return Response(res, status=200)

# shared forlder
@api_view(['GET'])
@require_auth
def api_get_shared_folders(request, user_id):
    """
    API để lấy danh sách các thư mục được chia sẻ với người dùng
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)
    
    allow_read_folders = Folder.objects.filter(permission__allow_read=user).exclude(owner=user)
    allow_write_folders = Folder.objects.filter(permission__allow_write=user).exclude(owner=user)
    
    folders = (allow_read_folders | allow_write_folders).distinct()
    folder_dict = [{'id': folder.id, 'name': folder.name, 'owner': folder.owner.username} for folder in folders]
    
    res = {
        'user_id': user_id,
        'shared_folders': folder_dict,
    }
    return Response(res, status=200)


@api_view(['POST'])
@require_auth
def api_sync_drive_folder(request, user_id, folder_id):
    """
    API để đảo ngược chuỗi
    """
    try:
        drive_folder_id = request.data.get('drive_folder_id', '')
        user = User.objects.filter(id=user_id).first()
        drive_acc_obj = CloudAccount.objects.filter(user=user).first()
        access_token = drive_acc_obj.credentials.get('access_token', '')
        
        # Call the reverse task
        result = sync_drive_folder_task.delay(user_id, folder_id, drive_folder_id, access_token)
        
        return Response({"task_id": result.id, "status": f"Folder:[{drive_folder_id}] sync task started for user_id {user_id}"}, status=202)
    except Exception as e:
        print("Error syncing drive folder:", str(e))
        return Response({"error": f"{str(e)}"}, status=500)


@api_view(['GET'])
@require_auth
def api_get_task_status(request, user_id, task_id):
    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        return Response({"status": "Pending"})
    elif task_result.state == 'SUCCESS':
        return Response({"status": "Success", "result": task_result.result})
    elif task_result.state == 'FAILURE':
        return Response({"status": "Failure", "error": str(task_result.result)})
    else:
        return Response({"status": task_result.state})
    


def renew_gg_access_token(user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    cloud_account_obj = CloudAccount.objects.filter(user=user, platform='google_drive').first()
    if not cloud_account_obj:
        return Response({"error": "Cloud account not found"}, status=404)

    refresh_token = cloud_account_obj.credentials.get('refresh_token', '')
    if not refresh_token:
        return Response({"error": "Refresh token missing"}, status=400)

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    response = requests.post(token_url, data=data)

    if response.status_code != 200:
        return Response({"error": "Failed to renew access token"}, status=500)

    new_tokens = response.json()
    new_access_token = new_tokens.get("access_token")

    # Update the stored access_token in credentials
    credentials = cloud_account_obj.credentials
    credentials["access_token"] = new_access_token
    credentials["expires_in"] = new_tokens.get("expires_in")  # Optional
    cloud_account_obj.credentials = credentials
    cloud_account_obj.save()

    return Response({"access_token": new_access_token, "expires_in": new_tokens.get("expires_in")})


@api_view(['POST'])
@require_auth
def api_create_sync_job(request, user_id):
    """
    Create a periodic task to sync Google Drive folder every 15 minutes
    """
    folder_drive_id = request.data.get('drive_folder_id')
    task_name = request.data.get('task_name', 'sync-drive-folder-every-15-minutes')
    interval = request.data.get('interval', 15)  # Default to 15 minutes if not provided
    
    if not user_id or not folder_drive_id:
        return Response({'error': 'user_id and drive_folder_id are required'}, status=400)
    
    cloud_account_obj = CloudAccount.objects.filter(user__id=user_id, platform='google_drive').first()
    if not cloud_account_obj:
        return Response({'error': 'Cloud account not found'}, status=404)
    access_token = cloud_account_obj.credentials.get('access_token', '')
    # Create or get the interval schedule
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=interval,
        period=IntervalSchedule.MINUTES,
    )
    
    # Create the periodic task
    task, created = PeriodicTask.objects.update_or_create(
        name=task_name,  # Lookup by unique name
        defaults={
            'interval': schedule,
            'task': 'applications.my_app.tasks.sync_drive_folder_task',
            'args': json.dumps([user_id, folder_drive_id, access_token]),
        }
    )
    res = {
        'task_name': task.name,
        'task_id': task.id,
        'user_id': user_id,
        'folder_drive_id': folder_drive_id,
        'interval': interval,
        'created': created
    }
    if not created:
        res.update({
            'message': 'Periodic task already exists, updated with new parameters'
        })
    else:
        res.update({
            'message': 'Periodic task created successfully'
        })
    return Response(res, status=201)
    