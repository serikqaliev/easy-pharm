from django.urls import path

from cart.views import add_to_cart, get_cart, remove_from_cart

urlpatterns = [
    path('', add_to_cart, name='add_to_cart'),
    path('/delete', remove_from_cart, name='remove_from_cart'),
    path('/list', get_cart, name='get_cart'),
]
