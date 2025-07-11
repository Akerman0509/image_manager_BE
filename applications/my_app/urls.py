

from django.urls import path, re_path, include

from . import views
from django.contrib.auth import views as auth_views




app_name = "my_app"
urlpatterns = [
    # get
    # path("authors/", views.getAuthor, name="getAuthor"),
    # path("books/", views.getBook, name="getBook"),
    # path("publishers/", views.getPublisher, name="getPublisher"),
    # path("categories/", views.getCategory, name="getCategory"),
    
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('', auth_views.LoginView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # /auth
    path('auth/register/', views.api_register, name='register'),
    path('auth/login/', views.api_login, name='login'),
    # /user
    re_path('users/(?P<user_id>[-\w\d]+)/detail/$', views.api_get_user_info, name='user_info'),
    # path('users/<int:user_id>/detail/', views.api_get_user_info, name='user_info'),
    
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/google/', views.GoogleLogin.as_view(), name='google_login'),
    
    
    # folder
    path('folder/create/', views.api_create_folder, name='create_folder'),
    
    

    # get img
    path('<int:user_id>/<int:folder_id>/images', views.api_get_images, name='get_img_list'),
    
    
    # upload + sync
    path('sync/save_drive_token/', views.api_save_drive_token, name='save_drive_token'),
    path('sync/img/', views.api_sync_img, name='sync_img'),
    path('upload/img/', views.api_upload_img, name='upload_img'),
    
    
]