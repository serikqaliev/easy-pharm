from django.urls import path
from users.views import (
    me_view, create_user, activate_user, change_avatar, create_contact_list, get_user_details, change_status,
    get_contacts, delete_contact, add_new_contact, get_privacy, get_settings, update_settings, update_privacy,
    delete_user, change_shortdesc, mute_user, block_user, update_contact, update_user_autosave, logout,
    get_common_groups, get_common_events, get_common_media, get_blocked_contacts
)

urlpatterns = [
    # Auth
    path('create_user/', create_user, name='create_user'),
    path('activate_user/', activate_user, name='activate_user'),
    path('change_avatar/', change_avatar, name='change_avatar'),
    path('change_shortdesc/', change_shortdesc, name='change_shortdesc'),
    path('logout/', logout, name='logout'),

    # User
    path('me/', me_view, name='me_view'),
    path('change_status/', change_status, name='change_status'),
    path('delete_user/', delete_user, name='delete_user'),

    # Privacy
    path('get_privacy/', get_privacy, name='get_privacy'),
    path('update_privacy/', update_privacy, name='update_privacy'),

    # Settings
    path('get_settings/', get_settings, name='get_settings'),
    path('update_settings/', update_settings, name='update_settings'),

    # Contacts / Getters
    path('get_user_details/<int:user_id>/', get_user_details, name='get_user_details'),
    path('get_contacts/<int:page>/', get_contacts, name='get_contacts'),
    path('get_blocked_contacts/', get_blocked_contacts, name='get_blocked_contacts'),

    # Contacts / Setters
    path('create_contact_list/', create_contact_list, name='create_contact_list'),
    path('add_new_contact/', add_new_contact, name='add_new_contact'),

    # Contacts / Mutators
    path('update_contact/', update_contact, name='update_contact'),
    path('mute_user/<int:user_id>/', mute_user, name='mute_user'),
    path('block_user/<int:user_id>/', block_user, name='block_user'),
    path('update_user_autosave/<int:user_id>/', update_user_autosave, name='update_user_autosave'),

    # Contacts / Deleters
    path('delete_contact/<int:contact_id>/', delete_contact, name='delete_contact'),

    # Media
    path('get_common_groups/<int:user_id>/', get_common_groups, name='get_common_groups'),
    path('get_common_events/<int:user_id>/', get_common_events, name='get_common_events'),
    path('get_common_media/<int:user_id>/', get_common_media, name='get_common_media'),
]
