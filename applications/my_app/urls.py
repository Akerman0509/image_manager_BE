

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
    path('user/<int:user_id>/home/', views.api_home_page, name='home'),
    
    path('user/<str:user_id>/shared/', views.api_get_shared_folders, name='shared'),
    
    
    # folder
    path('user/<int:user_id>/folder/create/', views.api_create_folder, name='create_folder'),
    path('user/<int:user_id>/folder/<int:folder_id>/change_permission/', views.api_change_folder_permission, name='change_folder_permission'),
    
    

    # get img
    path('user/<int:user_id>/folder/<int:folder_id>/images/', views.api_get_images, name='get_img_list'),
    
    
    # upload + sync
    path('user/<int:user_id>/sync/save_drive_token/', views.api_save_drive_token, name='save_drive_token'),
    path('user/<int:user_id>/sync/img/', views.api_sync_img, name='sync_img'),
    path('user/<int:user_id>/upload/img/', views.api_upload_image, name='upload_img'),
    path('user/<int:user_id>/image/<int:image_id>/', views.api_delete_image, name='delete_img'),

    
    # sync drive folder
    path('user/<int:user_id>/sync/folder/', views.api_sync_drive_folder, name='sync_drive_folder'),
    path('user/<int:user_id>/sync/folder/get_task_status/<str:task_id>/', views.api_get_task_status, name='api_get_task_status'),
    path('user/<int:user_id>/sync/folder/create_sync_job/', views.api_create_sync_job, name='api_create_sync_job'),
]