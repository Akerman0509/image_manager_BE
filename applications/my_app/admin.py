from django.contrib import admin

from .models import User, Folder, Image, FolderPermission, GGToken

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'email', 'created_at', 'updated_at')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    
@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'owner', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    list_filter = ('owner', 'parent')
    

    
@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ('folder', 'created_at')
    search_fields = ('folder__name', 'user__username')
    ordering = ('-created_at',)

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    list_filter = ('folder',)
    
@admin.register(GGToken)
class GGTokenAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'token', 'created_at')
    search_fields = ('user__username', 'token')
    ordering = ('-created_at',)