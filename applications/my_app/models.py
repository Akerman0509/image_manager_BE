from django.db import models
from django.utils import timezone
from datetime import timedelta


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
    password = models.CharField(max_length=255, null=True, blank=True)  # Store hashed passwords
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


class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subfolders')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)  
    
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.image.name} in {self.folder.name if self.folder else 'No Folder'}, uploaded by {self.user.username}"


class FolderPermission(models.Model):
    folder = models.OneToOneField(Folder, on_delete=models.CASCADE, related_name='permission')
    allow_read = models.ManyToManyField(User, related_name='read_permissions', blank=True)
    allow_write = models.ManyToManyField(User, related_name='write_permissions', blank=True)
    allow_delete = models.ManyToManyField(User, related_name='delete_permissions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Permissions for {self.folder.name}"


class DriveAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drive_accounts')
    access_token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    drive_email = models.EmailField()

    def __str__(self):
        return f"Drive Account for {self.user.username} ({self.drive_email})"
