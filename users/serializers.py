from rest_framework import serializers
from rest_framework.authtoken.models import Token

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField('get_token', read_only=True)

    @staticmethod
    def get_token(obj):
        token = Token.objects.get(user=obj)
        return token.key

    class Meta:
        model = User
        fields = [
            'id',
            'token',
            'username',
            'phone',
            'created_at',
            'updated_at',
            'is_registered',
            'is_staff',
        ]
