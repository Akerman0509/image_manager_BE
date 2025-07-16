

from rest_framework import serializers
from .models import User, Image, Folder, GGToken, Folder, FolderPermission
from applications.commons.utils import hash_password


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("username already exists.")
        if not data.get('username'):
            raise serializers.ValidationError("username is required.")
        if not data.get('password'):
            raise serializers.ValidationError("Password is required.")
        # if len(data['password']) < 8:
        #     raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        return data

    def create(self, validated_data):
        raw_password = validated_data.get('password')  
        hashed_password = hash_password(raw_password)
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            password=hashed_password
        )
        
        user.save()
        return user
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "created_at": instance.created_at,
        }



class LoginSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):

        email = data.get('email')
        if not email:
            raise serializers.ValidationError("email is required.")
        password = data.get('password')
        if not password:
            raise serializers.ValidationError("Password is required.")
        return data
        
        

        

    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "username": instance.username,
            "email": instance.email,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at
        }
        
        
class GGTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = GGToken
        fields = ['id', 'user', 'token']
    
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "user": instance.user.id,
            "token": instance.token
        }
        
class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        parent = validated_data.get('parent')
        if parent and not Folder.objects.filter(id=parent.id).exists():
            raise serializers.ValidationError("Parent folder does not exist.")
        
        folder = Folder(
            name=validated_data['name'],
            parent=parent,
            owner=validated_data['owner']
        )
        folder.save()
        
        # create folderPermission for the owner
        folder_permission = FolderPermission.objects.create(folder=folder)
        # Set many-to-many relationships
        owner = validated_data['owner']
        folder_permission.allow_read.set([owner])
        folder_permission.allow_write.set([owner])
        folder_permission.allow_delete.set([owner])
        folder_permission.save()
        
        
        return folder
    
    def to_representation(self, instance):
        return {
            "id": instance.id,
            "name": instance.name,
            "parent": instance.parent.id if instance.parent else None,
            "owner": instance.owner.id,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at
        }
        
# class FolderPermissionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = FolderPermission
#         fields = ['id', 'folder', 'user', 'created_at']
    
#     def to_representation(self, instance):
#         return {
#             "id": instance.id,
#             "folder": instance.folder.id,
#             "user": instance.user.id,
#             "created_at": instance.created_at
#         }