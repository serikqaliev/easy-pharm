from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone',
            'created_at',
            'updated_at',
            'is_active',
            'is_staff',
        ]
