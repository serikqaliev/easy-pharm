from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from categories.models import Category
from medicines.models import Medicine
from medicines.serializers import MedicineSerializer
from symptoms.models import Symptom
from symptoms.serializers import SymptomSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def create_medicine(request):
    name = request.data['name']
    description = request.data['description']
    price = request.data['price']
    image = request.data.get('image', None)
    category_id = request.data.get('category_id', None)

    category = get_object_or_404(Category, id=category_id) if category_id else None

    medicine = Medicine.objects.create(
        name=name,
        description=description,
        price=price,
        image=image,
        category=category
    )
    serializer = MedicineSerializer(medicine, context={'request': request}).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def delete_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    medicine.delete()

    return Response({}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_medicines(request):
    data = request.data
    search = data.get('search', '')
    symptoms_ids = data.get('symptoms_ids', [])
    category_id = data.get('category_id', None)
    price_from = data.get('price_from', None)
    price_to = data.get('price_to', None)

    medicines = Medicine.objects.filter(name__icontains=search)

    if symptoms_ids:
        medicines = medicines.filter(symptoms__id__in=symptoms_ids)

    if category_id:
        medicines = medicines.filter(category_id=category_id)

    if price_from:
        medicines = medicines.filter(price__gte=price_from)

    if price_to:
        medicines = medicines.filter(price__lte=price_to)

    medicines = medicines.distinct()
    serializer = MedicineSerializer(medicines, context={'request': request}, many=True).data

    return Response({'medicines': serializer}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def update_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    medicine.name = request.data['name']
    medicine.description = request.data['description']
    medicine.price = request.data['price']
    medicine.image = request.data.get('image', None)

    category_id = request.data.get('category_id', None)
    medicine.category = get_object_or_404(Category, id=category_id) if category_id else None

    medicine.save()

    serializer = MedicineSerializer(medicine, context={'request': request}).data

    return Response({'medicine': serializer}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def add_symptoms_to_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    symptom_ids = request.data['symptom_ids']
    symptoms = Symptom.objects.filter(id__in=symptom_ids)

    for symptom in symptoms:
        medicine.symptoms.add(symptom)

    serializer = MedicineSerializer(medicine, context={'request': request}).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def remove_symptom_from_medicine(request, medicine_id, symptom_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    symptom = get_object_or_404(Symptom, id=symptom_id)

    medicine.symptoms.remove(symptom)

    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def get_symptoms_of_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    symptoms = medicine.symptoms.all()

    serializer = SymptomSerializer(symptoms, many=True).data

    return Response(serializer, status=status.HTTP_200_OK)


