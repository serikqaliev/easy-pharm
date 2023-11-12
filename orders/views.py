from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from medicines.models import Medicine
from orders.models import Cart, Order


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    order_items = request.data['order_items']  # {medicine_id, quantity}
    address = request.data['address']

    order_items_to_create = []
    not_found_medicines = []

    for order_item in order_items:
        medicine = Medicine.objects.get(id=order_item['medicine_id'])
        if not medicine:
            not_found_medicines.append(order_item['medicine_id'])
            continue

        order_items_to_create.append(
            Cart(
                medicine=medicine,
                quantity=order_item['quantity']
            )
        )

    Cart.objects.bulk_create(order_items_to_create)
    Order.objects.create(
        user=request.user,
        address=address
    )

    return Response({
        'not_found_medicines': not_found_medicines,
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()

    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return Response({}, status=status.HTTP_200_OK)
