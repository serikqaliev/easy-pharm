from rest_framework import serializers

from categories.serializers import CategorySerializer
from medicines.models import Medicine


class MedicineSerializer(serializers.ModelSerializer):
    last_three_symptoms = serializers.SerializerMethodField('get_last_three_symptoms', read_only=True)
    category = serializers.SerializerMethodField('get_category', read_only=True)
    image = serializers.SerializerMethodField('get_image', read_only=True)

    def get_image(self, obj):
        if obj.image:
            return self.context.get('request').build_absolute_uri(obj.image.url)
        return None

    @staticmethod
    def get_category(obj):
        """Set category's name of medicine"""
        if obj.category is None:
            return None
        return CategorySerializer(obj.category).data

    @staticmethod
    def get_last_three_symptoms(obj):
        """Set last three symptom's name of medicine"""
        symptoms = obj.symptoms.all().order_by('-id')[:3]
        names = [symptom.name for symptom in symptoms]
        return names

    class Meta:
        model = Medicine
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'last_three_symptoms',
            'category',
            'created_at',
            'updated_at',
        ]


