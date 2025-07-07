from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.

# // User
# User
# Name
# Email
# Password (hashed)
# CreatedAt
# UpdatedAt

class UserManager(models.Manager):
    def create_gg_user(self, username, email):
        return self.model.objects.create(
            username=username,
            email=email,
            account_type=User.AccountType.GG_AUTH
        )

class User(models.Model):
    
    class AccountType(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        GG_AUTH = 'gg_auth', 'gg_auth'
        

    username = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)  # Store hashed passwords
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.NORMAL
    )
    
    objects = UserManager()
    def __str__(self):
        return self.username
    
    
class GGToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gg_tokens')
    token = models.CharField(max_length=255, null=True, blank=True)  # Google Drive token
    created_at = models.DateTimeField(auto_now_add=True)   
    

    def __str__(self):
        return f"GG Token for {self.user.username} "

# // Folder
# Folder
# ID
# Name
# ParentID (nullable, for root folders)
# Owner_id (FK to User)
# CreatedAt
# UpdatedAt

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subfolders')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# // Image
# Image
# ID
# Name
# FolderID (nullable, for root images)
# CreatedAt
# UpdatedAt

class Image(models.Model):
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# //FolderPermission
# ID
# FolderID (OneToOne to Folder)
# AllowRead [user_id, user_id, ....]
# AllowWrite [user_id, user_id, ....]
# AllowDelete [user_id, user_id, ....]

class FolderPermission(models.Model):
    folder = models.OneToOneField(Folder, on_delete=models.CASCADE, related_name='permission')
    allow_read = models.ManyToManyField(User, related_name='read_permissions', blank=True)
    allow_write = models.ManyToManyField(User, related_name='write_permissions', blank=True)
    allow_delete = models.ManyToManyField(User, related_name='delete_permissions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Permissions for {self.folder.name}"


# // DriveAccount
# DriveAccount
# UserID (FK to User)
# AccessToken
# RefreshToken
# token_expire
# CreatedAt
# drive_email

# 1 User can have multiple DriveAccounts (e.g. for different Google accounts)

# class DriveAccount(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drive_accounts')
#     access_token = models.CharField(max_length=255)
#     refresh_token = models.CharField(max_length=255)
#     token_expire = models.DateTimeField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     drive_email = models.EmailField()

#     def __str__(self):
#         return f"Drive Account for {self.user.name} ({self.drive_email})"

# # // DriveImage
# # DriveImage
# # img_id (FK to Image)

# # drive_account_id (FK to DriveAccount)
# # drive_file_id (Google Drive file ID)

# # synced_at datetime

# class DriveImage(models.Model):
#     image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='drive_images')
#     drive_account = models.ForeignKey(DriveAccount, on_delete=models.CASCADE, related_name='drive_images')
#     drive_file_id = models.CharField(max_length=255)
#     synced_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Drive Image {self.image.name} for {self.drive_account.drive_email}"