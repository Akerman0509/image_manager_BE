from django.contrib import admin

from .models import User, Folder, Image, CloudAccount, FolderPermission
from django.utils.safestring import mark_safe
from django.urls import reverse
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'email', 'created_at', 'updated_at')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    
    

class ImageInline(admin.TabularInline):
    model = Image
    extra = 0
    readonly_fields = ('image_link', 'created_at', 'updated_at')
    fields = ('image_link', 'created_at', 'updated_at')

    def image_link(self, obj):
        if obj.pk:
            # Get admin URL to change this Image object
            url = reverse('admin:my_app_image_change    ', args=[obj.pk])
            return mark_safe(f'<a href="{url}" target="_blank">{obj.image.name}</a>')
        return "-"
    image_link.short_description = "Image File"
        

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    
    inlines = [ImageInline]
    
    list_display = ('id','name', 'parent', 'owner')
    search_fields = ('name',)
    list_filter = ('owner', 'parent')
    

    
# @admin.register(FolderPermission)
# class FolderPermissionAdmin(admin.ModelAdmin):
#     list_display = ('folder', 'created_at')
#     search_fields = ('folder__name', 'user__username')
#     ordering = ('-created_at',)

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id','user__username', 'user__id', 'folder', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    list_filter = ('folder',)
    

    
@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ('folder__id','folder_name', 'read_users', 'write_users', 'delete_users', 'created_at')
    search_fields = ('folder__name',)
    ordering = ('-created_at',)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @admin.display(description='Folder Name')
    def folder_name(self, obj):
        return obj.folder.name if obj.folder else "No Folder"

    @admin.display(description='Read Users')
    def read_users(self, obj):
        return ", ".join(user.email for user in obj.allow_read.all())

    @admin.display(description='Write Users')
    def write_users(self, obj):
        return ", ".join(user.email for user in obj.allow_write.all())

    @admin.display(description='Delete Users')
    def delete_users(self, obj):
        return ", ".join(user.email for user in obj.allow_delete.all())


    
    
@admin.register(CloudAccount)
class DriveAccountAdmin(admin.ModelAdmin):
    list_display = ('id','user__username', 'drive_email', 'credentials', 'created_at', )
    search_fields = ('user__username', 'drive_email')
    ordering = ('-created_at',)
    
    def drive_email(self, obj):
        return obj.user.email if obj.user else "No User"
    drive_email.short_description = "Drive Email"
    
