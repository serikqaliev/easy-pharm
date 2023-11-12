from django.urls import path

from categories.views import create_category, get_categories, update_category, delete_category

urlpatterns = [
    path('', create_category, name='create_category'),
    path('/list', get_categories, name='get_categories'),
    path('/<int:category_id>', update_category, name='update_category'),
    path('/<int:category_id>/delete', delete_category, name='delete_category'),
]
