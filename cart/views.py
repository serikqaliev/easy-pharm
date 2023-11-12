from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from medicines.models import Medicine
from medicines.serializers import MedicineSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    medicine_id = request.data['medicine_id']

    medicine = get_object_or_404(Medicine, id=medicine_id)
    cart_item = request.user.carts.filter(medicine=medicine).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item = request.user.carts.create(
            medicine=medicine,
            quantity=1
        )

    medicine_serialized = MedicineSerializer(medicine, context={'request': request}).data

    return Response({
        'medicine': medicine_serialized,
        'quantity': cart_item.quantity,
        'updated_at': cart_item.updated_at
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    medicine_id = request.data['medicine_id']

    medicine = get_object_or_404(Medicine, id=medicine_id)
    cart_item = request.user.carts.filter(medicine=medicine).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    medicine_serialized = MedicineSerializer(medicine, context={'request': request}).data

    if cart_item.quantity == 0:
        return Response(None, status=status.HTTP_200_OK)

    cart_serialized = {
        'medicine': medicine_serialized,
        'quantity': cart_item.quantity,
        'updated_at': cart_item.updated_at
    }

    return Response(cart_serialized, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart_items = request.user.carts.all()

    medicines = []
    for cart_item in cart_items:
        medicine = MedicineSerializer(cart_item.medicine, context={'request': request}).data
        medicines.append({
            'medicine': medicine,
            'quantity': cart_item.quantity,
            'updated_at': cart_item.updated_at
        })

    return Response(medicines, status=status.HTTP_200_OK)
