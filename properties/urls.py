from django.urls import path
from properties.views import timezone_list, countrycodes_list

urlpatterns = [
    path('timezone_list/', timezone_list, name='timezone_list'),
    path('countrycodes_list/', countrycodes_list, name='countrycodes_list')
]
