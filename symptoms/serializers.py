from rest_framework import serializers

from symptoms.models import Symptom


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = [
            'id',
            'name',
            'description'
        ]