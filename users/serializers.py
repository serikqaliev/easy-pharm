from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'username',
            'phone',
            'time_zone',
            'avatar',
            'created_at',
            'updated_at',
            'status_change_at',
            'is_active',
            'is_online',
            'status',
            'in_calendaria',
        ]
