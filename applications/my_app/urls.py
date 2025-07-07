

from django.urls import path, re_path

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
    # path('token/', views.api_login_with_gg, name='api_login_with_gg'),
    
    # /auth
    path('auth/register/', views.api_register, name='register'),
    path('auth/login/', views.api_login, name='login'),
    
    
    
    # /user
    re_path('users/(?P<user_id>[-\w\d]+)/detail/$', views.api_get_user_info, name='user_info'),
    # path('users/<int:user_id>/detail/', views.api_get_user_info, name='user_info'),
]