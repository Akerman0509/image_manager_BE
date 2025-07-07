

from rest_framework import serializers
from .models import User, Image, Folder, FolderPermission, GGToken
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


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):

        username = data.get('username')
        if not username:
            raise serializers.ValidationError("Username is required.")
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