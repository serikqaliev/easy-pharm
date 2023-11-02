from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from medicines.models import Medicine
from medicines.serializers import MedicineSerializer
from users.permissions.staff_permission import IsStaff


@api_view(['POST'])
@permission_classes((IsAuthenticated, IsStaff))
def create_medicine(request):
    name = request.data['name']
    description = request.data['description']
    price = request.data['price']
    image = request.data.get('image', None)

    medicine = Medicine.objects.create(
        name=name,
        description=description,
        price=price,
        image=image
    )
    serializer = MedicineSerializer(medicine).data

    return Response({'medicine': serializer}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaff])
def delete_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    medicine.delete()

    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes(IsAuthenticated)
def get_medicines(request):
    medicines = Medicine.objects.all()
    serializer = MedicineSerializer(medicines, many=True).data

    return Response({'medicines': serializer}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaff])
def update_medicine(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    medicine.name = request.data['name']
    medicine.description = request.data['description']
    medicine.price = request.data['price']
    medicine.image = request.data.get('image', None)

    medicine.save()

    serializer = MedicineSerializer(medicine).data

    return Response({'medicine': serializer}, status=status.HTTP_200_OK)



