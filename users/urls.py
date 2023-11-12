from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from users.views import (
    me_view, create_user, activate_user, delete_user, logout, verify_user,
)

urlpatterns = [
    # Auth
    path('/verify', verify_user, name='api_token_auth'),
    path('/create', create_user, name='create_user'),
    path('/activate', activate_user, name='activate_user'),
    path('/logout', logout, name='logout'),

    # User
    path('/me', me_view, name='me_view'),
    path('/delete', delete_user, name='delete_user'),
]
