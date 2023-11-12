from django.urls import path

from symptoms.views import create_symptom, delete_symptom, update_symptom, get_symptoms, delete_by_ids

urlpatterns = [
    path('', create_symptom, name='create_symptom'),
    path('/<int:symptom_id>', delete_symptom, name='delete_symptom'),
    path('/<int:symptom_id>', update_symptom, name='update_symptom'),
    path('/list', get_symptoms, name='get_symptoms'),
    path('/delete_by_ids', delete_by_ids, name='delete_by_ids')
]
