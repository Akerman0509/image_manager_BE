

from django.urls import path, re_path, include

from . import views
from django.contrib.auth import views as auth_views




app_name = "my_app"
urlpatterns = [
    # /auth
    path('auth/register/', views.api_register, name='register'),
    path('auth/login/', views.api_login, name='login'),
    path ('auth/gg_login/', views.api_login_with_gg, name='login_with_gg'),
    
    # /user
    re_path('user/(?P<user_id>[-\w\d]+)/detail/$', views.api_get_user_info, name='user_info'),
    path('user/home/', views.api_home_page, name='home'),
    
    path('user/shared/', views.api_get_shared_folders, name='shared'),
    
    
    # folder
    ## CREATE
    path('user/folder/create/', views.api_create_folder, name='create_folder'),
    ## CHANGE PERMISSION
    path('user/folder/<int:folder_id>/change_permission/', views.api_change_folder_permission, name='change_folder_permission'),
    ## DELETE
    path('user/folder/<int:folder_id>/', views.api_delete_folder, name='delete_folder'),
    
    ## SYNC DRIVE FOLDER
    path('user/sync/folder/', views.api_sync_drive_folder, name='sync_drive_folder'),
    ## SYNC MINIO FOLDER
    path('user/sync/minio/folder/', views.api_sync_minIO_folder, name='sync_minIO_folder'),

    ### GET SYNC STATUS
    path('user/<int:user_id>/sync/folder/get_task_status/<str:task_id>/', views.api_get_task_status, name='api_get_task_status'),
    ### CREATE SYNC JOB (WRITE TO DB)
    path('user/<int:user_id>/sync/folder/create_sync_job/', views.api_create_sync_job, name='api_create_sync_job'),
    

    # IMAGE
    ## GET
    path('user/folder/<int:folder_id>/images/', views.api_get_images, name='get_images'),
    ## DELETE
    path('user/folder/<int:folder_id>/image/<int:image_id>/', views.api_delete_images, name='delete_img'),
    
    
    # upload
    path('user/sync/save_drive_token/', views.api_save_drive_token, name='save_drive_token'),
    path('user/upload/img/', views.api_upload_image, name='upload_img'),
    # SYNC MINIO
    path('user/sync/img/', views.api_sync_img, name='sync_img'),
    
    
    # renew gg token
    # path('user/<int:user_id>/renew_gg_token/', views.api_renew_gg_token, name='renew_gg_token'),

    
    
    # gg photo flow
    
    path('user/<int:user_id>/gg_photo/<str:image_id>/', views.api_download_google_photo_by_id, name='download_gg_photo'),

]