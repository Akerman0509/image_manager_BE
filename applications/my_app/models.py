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
    
    

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subfolders')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    drive_folder_id = models.CharField(max_length=255, null=True, blank=True)  # Google Drive folder ID
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Create permissions for new folder
            permission, created = FolderPermission.objects.get_or_create(folder=self)
            if created:
                permission.allow_read.set([self.owner])
                permission.allow_write.set([self.owner])
                permission.allow_delete.set([self.owner])


    def __str__(self):
        return self.name

class FolderPermission(models.Model):
    folder = models.OneToOneField(Folder, on_delete=models.CASCADE, related_name='permission')
    allow_read = models.ManyToManyField(User, related_name='read_permissions', blank=True)
    allow_write = models.ManyToManyField(User, related_name='write_permissions', blank=True)
    allow_delete = models.ManyToManyField(User, related_name='delete_permissions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Permissions for {self.folder.name}"
    

class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)  
    
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='images')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.image.name} in {self.folder.name if self.folder else 'No Folder'}, uploaded by {self.user.username}"





class CloudAccount(models.Model):
    PLATFORM_CHOICES = [
        ('google_drive', 'Google Drive'),
        ('s3', 'Amazon S3'),
        ('dropbox', 'Dropbox'),
        # etc.
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloud_accounts')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    credentials = models.JSONField()  # Store tokens/keys here
    drive_email = models.EmailField(blank=True, null=True)
    account_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Drive Account for {self.user.username} ({self.drive_email})"




# credentials = models.JSONField()  # Store tokens/keys here
# // For Google Drive
# {
#   "access_token": "...",
#   "refresh_token": "...",
#   "expires_in": 3600
# }

# // For S3
# {
#   "access_key_id": "...",
#   "secret_access_key": "...",
#   "session_token": "..."
# }
