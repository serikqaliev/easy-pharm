from django.urls import path

from medicines.views import (
    create_medicine, delete_medicine, get_medicines, update_medicine
)

urlpatterns = [
    # Auth
    path('', create_medicine, name='create_medicine'),
    path('/<int:medicine_id>', update_medicine, name='delete_medicine'),
    path('/list', get_medicines, name='get_medicines'),
    path('/<int:medicine_id>', delete_medicine, name='delete_medicine'),
]
