from asgiref.sync import sync_to_async
from rest_framework import serializers

from chat.models import Member
from users.serializers import ShortUserSerializer


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField('user_set', read_only=True)
    participation_status = serializers.SerializerMethodField('participation_status_set', read_only=True)

    def user_set(self, instance):
        user = instance.user
        serializer = ShortUserSerializer(user, context={"user": self.context.get("user")})
        return serializer.data

    @staticmethod
    def participation_status_set(instance):
        return instance.status

    async def async_serialization(self, instance, user):
        self.context['user'] = user
        user_data = await sync_to_async(self.user_set)(instance)

        return {
            'id': instance.id,
            'user': user_data,
            'role': instance.role,
            'participation_status': instance.status,
        }

    class Meta:
        model = Member
        fields = [
            'id',
            'user',
            'role',
            'participation_status',
        ]


class ChatMemberSerializer(serializers.ModelSerializer):
    user_data = serializers.SerializerMethodField('user_set', read_only=True)

    def user_set(self, instance):
        user = instance.user
        serializer = ShortUserSerializer(user, context={"user": self.context.get("user")})
        return serializer.data

    class Meta:
        model = Member
        fields = ['user_data']
