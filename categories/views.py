from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from categories.models import Category
from medicines.serializers import CategorySerializer


# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def create_category(request):
    name = request.data['name']

    already_exists = Category.objects.filter(name=name).exists()
    if already_exists:
        return Response({'error': 'Category already exists'}, status=status.HTTP_400_BAD_REQUEST)

    category = Category.objects.create(name=name)
    serializer = CategorySerializer(category).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories(request):
    categories = Category.objects.all().order_by('name')
    serializer = CategorySerializer(categories, many=True).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def update_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    name = request.data['name']

    category.name = name
    category.save()

    serializer = CategorySerializer(category).data

    return Response(serializer, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # TODO: Add IsStaff permission
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()

    return Response({}, status=status.HTTP_200_OK)
