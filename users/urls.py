from django.urls import path
from users.views import (
    me_view, create_user, activate_user, change_avatar, get_user_details, delete_user, logout,
)

urlpatterns = [
    # Auth
    path('create_user/', create_user, name='create_user'),
    path('activate_user/', activate_user, name='activate_user'),
    path('change_avatar/', change_avatar, name='change_avatar'),
    path('logout/', logout, name='logout'),

    # User
    path('me/', me_view, name='me_view'),
    path('delete_user/', delete_user, name='delete_user'),
]
