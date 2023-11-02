from django.urls import path

from events.views import create_event, add_attachment, invite_users, get_event_details, \
    get_events, get_events_by_date, get_events_month, change_remind, delete_user, change_permission, \
    create_event_on_chat, delete_event, get_event_history, \
    delete_attachment, leave_event, get_attachments, \
    delete_attachments, create_chat_on_event, delete_chat_on_event, edit_event, get_inbox, \
    get_accepted_events, add_links, get_links, delete_all_events, invitation_respond, delete_link

urlpatterns = [
    # --- Event --- #
    path('create_event/', create_event, name='create_event'),
    path('get_event_details/<int:event_id>/', get_event_details, name='get_event_details'),
    path('get_events/', get_events, name='get_events'),
    path('get_events_by_date/<int:day>/<int:month>/<int:year>/', get_events_by_date, name='get_events_by_date'),
    path('get_events_month/<int:month>/<int:year>/', get_events_month, name='get_events_month'),
    path('get_accepted_events/', get_accepted_events, name='get_accepted_events'),
    path('edit_event/<int:event_id>/', edit_event, name='edit_event'),
    path('delete_event/', delete_event, name='delete_event'),
    path('delete_all_events/', delete_all_events, name='delete_all_events'),

    # --- Invites --- #
    path('invite_users/', invite_users, name='invite_users'),
    path('invitation_respond/<int:invite_id>/', invitation_respond, name='invitation_respond'),
    path('change_remind/', change_remind, name='change_remind'),
    path('delete_user/', delete_user, name='delete_user'),
    path('change_permission/', change_permission, name='change_permission'),
    path('leave_event/<int:event_id>/', leave_event, name='leave_event'),
    path('get_inbox/', get_inbox, name='get_inbox'),

    # --- Attachments --- #
    path('add_attachment/', add_attachment, name='add_attachment'),
    path('get_attachments/<int:event_id>/', get_attachments, name='get_attachments'),
    path('delete_attachments/', delete_attachments, name='delete_attachments'),
    path('delete_attachment/', delete_attachment, name='delete_attachment'),

    # --- Links --- #
    path('add_links/', add_links, name='add_links'),
    path('get_links/<int:event_id>/', get_links, name='get_links'),
    path('delete_link/<int:link_id>/', delete_link, name='delete_link'),

    # --- Chat --- #
    path('create_event_on_chat/<int:chat_id>/', create_event_on_chat, name='create_event_on_chat'),
    path('create_chat_on_event/<int:event_id>/', create_chat_on_event, name='create_chat_on_event'),
    path('delete_chat_on_event/<int:event_id>/', delete_chat_on_event, name='delete_chat_on_event'),

    # --- History --- #
    path('get_event_history/<int:event_id>/', get_event_history, name='get_event_history'),
]
