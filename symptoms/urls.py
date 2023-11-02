from django.urls import path

from symptoms.views import create_symptom

urlpatterns = [
    path('', create_symptom, name='create_symptom'),
]
