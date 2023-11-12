from rest_framework import serializers

from medicines.serializers import MedicineSerializer
from orders.models import Order, CartItem


class OrderSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField('get_order_items', read_only=True)

    @staticmethod
    def get_order_items(obj):
        return OrderItemSerializer(obj.order_items, many=True).data

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'address',
            'order_items',
            'created_at',
            'updated_at',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    medicine = serializers.SerializerMethodField('get_medicine', read_only=True)

    @staticmethod
    def get_medicine(obj):
        return MedicineSerializer(obj.medicine).data

    class Meta:
        model = CartItem
        fields = [
            'id',
            'medicine',
            'quantity',
        ]