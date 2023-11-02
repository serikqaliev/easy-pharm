from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from symptoms.models import Symptom
from symptoms.serializers import SymptomSerializer
from users.permissions.staff_permission import IsStaff


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaff])
def create_symptom(request):
    name = request.data['name']
    description = request.data['description']

    symptom = Symptom.objects.create(
        name=name,
        description=description
    )

    serializer = SymptomSerializer(symptom).data

    return Response({'symptom': serializer}, status=status.HTTP_200_OK)
