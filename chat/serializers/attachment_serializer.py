from rest_framework import serializers

from chat.models import Attachment, ContactMessageAttachment, Link


class AddImageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class MediaAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class ContactAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessageAttachment
        fields = '__all__'


class EventAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class LocationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'
