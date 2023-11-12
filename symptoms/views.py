from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from symptoms.models import Symptom
from symptoms.serializers import SymptomSerializer
from users.permissions.staff_permission import IsStaff


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def create_symptom(request):
    name = request.data['name']
    description = request.data['description']

    symptom = Symptom.objects.create(
        name=name,
        description=description
    )

    serializer = SymptomSerializer(symptom).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def delete_symptom(request, symptom_id):
    symptom = get_object_or_404(Symptom, id=symptom_id)
    symptom.delete()

    return Response({'message': 'Symptom deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def update_symptom(request, symptom_id):
    symptom = get_object_or_404(Symptom, id=symptom_id)

    name = request.data['name']
    description = request.data['description']

    symptom.name = name
    symptom.description = description

    symptom.save()

    serializer = SymptomSerializer(symptom).data

    return Response({'symptom': serializer}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def get_symptoms(request):
    symptoms = Symptom.objects.all()

    serializer = SymptomSerializer(symptoms, many=True).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def delete_by_ids(request):
    symptoms_ids = request.data['symptoms_ids']

    symptoms = Symptom.objects.filter(id__in=symptoms_ids)
    symptoms.delete()

    return Response({}, status=status.HTTP_200_OK)