from django.urls import path

from orders.views import create_order

urlpatterns = [
    path('', create_order, name='create_order'),
    # path('/<int:order_id>', delete_order, name='delete_order'),
    # path('/<int:order_id>', get_order, name='get_order'),
    # path('/list', get_orders, name='get_orders'),
    # path('/<int:order_id>/status', update_order_status, name='update_order_status'),
]
