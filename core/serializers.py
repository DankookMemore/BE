from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Board, Memo
from django.contrib.auth.models import User 

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'nickname', 'email']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_username(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("유효한 이메일 주소를 입력해주세요.")
        return value

    def validate_password(self, value):
        import re
        if len(value) < 8 or not re.search(r'[A-Z]', value) or not re.search(r'[a-z]', value) \
           or not re.search(r'[0-9]', value) or not re.search(r'[\W_]', value):
            raise serializers.ValidationError(
                "비밀번호는 대소문자, 숫자, 특수문자를 포함해 8자 이상이어야 합니다."
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            nickname=validated_data['nickname'],
            email=validated_data['email'],
        )
        return user


class BoardSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'category', 'summary', 'is_completed',
            'user', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MemoSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Memo
        fields = ['id', 'board', 'content', 'timestamp', 'is_finished', 'summary', 'user']
        read_only_fields = ['id', 'timestamp', 'summary', 'user']
