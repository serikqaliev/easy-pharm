from rest_framework import serializers
from medicines.models import Medicine, Symptom


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'created_at',
            'updated_at',
        ]