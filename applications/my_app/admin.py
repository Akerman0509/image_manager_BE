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
            url = reverse('admin:my_app_image_change', args=[obj.pk])
            return mark_safe(f'<a href="{url}" target="_blank">{obj.image.name}</a>')
        return "-"
    image_link.short_description = "Image File"
        

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    
    inlines = [ImageInline]
    
    list_display = ('id','name', 'parent', 'owner')
    search_fields = ('name',)
    list_filter = ('owner', 'parent')
    def delete_queryset(self, request, queryset):
        for folder in queryset:
            for img in folder.images.all():
                if img.image:
                    img.image.delete(save=False)  # delete file
                img.delete()  # delete DB record
            folder.delete()  # finally delete the folder
    

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id','image_name', 'user__username', 'user__id', 'folder', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    list_filter = ('folder',)
    

    
@admin.register(FolderPermission)
class FolderPermissionAdmin(admin.ModelAdmin):
    list_display = ('folder__id', 'folder__owner__username','folder__name', 'user__username', 'allow_read', 'allow_write', 'allow_delete')
    search_fields = ('folder__name',)
    ordering = ('-created_at',)

    
    
@admin.register(CloudAccount)
class DriveAccountAdmin(admin.ModelAdmin):
    list_display = ('id','user__username', 'drive_email', 'credentials', 'created_at', )
    search_fields = ('user__username', 'drive_email')
    ordering = ('-created_at',)
    
    def drive_email(self, obj):
        return obj.user.email if obj.user else "No User"
    drive_email.short_description = "Drive Email"
    
