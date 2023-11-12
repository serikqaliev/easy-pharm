from django.urls import path

from medicines.views import (
    create_medicine, delete_medicine, get_medicines, update_medicine, add_symptoms_to_medicine,
    remove_symptom_from_medicine, get_symptoms_of_medicine
)

urlpatterns = [
    # Medicine
    path('', create_medicine, name='create_medicine'),
    path('/<int:medicine_id>', update_medicine, name='delete_medicine'),
    path('/list', get_medicines, name='get_medicines'),
    path('/<int:medicine_id>/delete', delete_medicine, name='delete_medicine'),  # TODO: find way to use DELETE method

    # Symptom
    path('/<int:medicine_id>/symptoms', add_symptoms_to_medicine, name='add_symptom_to_medicine'),
    path('/<int:medicine_id>/symptoms/<int:symptom_id>', remove_symptom_from_medicine, name='remove_symptom_from_medicine'),
    path('/<int:medicine_id>/symptoms/list', get_symptoms_of_medicine, name='get_symptoms_of_medicine'),
]
