from django.urls import path
import chat.views

urlpatterns = [
    path('<int:chat_id>/lobby/', chat.views.lobby),

    # --- Chats --- #
    path('', chat.views.get_chats, name='get_chats'),
    path('direct/', chat.views.create_direct_chat, name='create_direct_chat'),
    path('group/', chat.views.create_group_chat, name='create_group_chat'),
    path('event/', chat.views.create_event_chat, name='create_event_chat'),
    path('<int:chat_id>/', chat.views.get_chat, name='get_chat'),
    path('<int:chat_id>/', chat.views.update_group_chat, name='update_group_chat'),
    path('<int:chat_id>/delete/', chat.views.delete_chat, name='delete_chat'),
    path('<int:chat_id>/<str:action>/', chat.views.action_on_chat, name='action_on_chat'),

    # --- Members --- #
    path('<int:chat_id>/join/', chat.views.join_chat, name='join_chat'),
    path('<int:chat_id>/members/kick/', chat.views.kick_member, name='kick_member'),
    path('<int:chat_id>/leave/', chat.views.leave_chat, name='leave_chat'),
    path('<int:chat_id>/members/invite/', chat.views.invite_members, name='invite_members'),
    path('<int:chat_id>/members/list/', chat.views.get_members, name='get_members'),
    path('<int:chat_id>/members/role/', chat.views.change_member_role, name='change_member_role'),

    # --- Messages --- #
    path('<int:chat_id>/messages', chat.views.send_message, name='send_message'),  # POST
    path('<int:chat_id>/messages/list/', chat.views.get_messages, name='get_messages'),  # POST
    path('<int:chat_id>/messages/<int:message_id>/read/', chat.views.mark_read, name='mark_read'),
    path('<int:chat_id>/messages/<int:message_id>/pin/', chat.views.pin_unpin_message, name='action_on_message'),
    path('<int:chat_id>/messages/<int:message_id>/', chat.views.delete_message, name='delete_message'),  # DELETE
    path('<int:chat_id>/messages/truncate/', chat.views.truncate_chat, name='truncate_chat'),  # DELETE

    # --- Attachments --- #
    path('<int:chat_id>/attachments/media/list/', chat.views.get_chat_attached_media, name='get_chat_attached_images'),
    path('<int:chat_id>/attachments/contacts/list/', chat.views.get_chat_attached_contacts, name='get_chat_attached_contacts'),
    path('<int:chat_id>/attachments/events/list/', chat.views.get_chat_attached_events, name='get_chat_attached_events'),
    path('<int:chat_id>/attachments/locations/list/', chat.views.get_chat_attached_locations, name='get_chat_attached_locations'),
    path('<int:chat_id>/attachments/links/list/', chat.views.get_chat_attached_links, name='get_chat_attached_links'),
    # --- Attachments : Uploaders --- #
    path('<int:chat_id>/attachments/media/', chat.views.upload_attachment, name='upload_attachment'),  # POST
    # --- Attachments : Deleters --- #
    path('<int:chat_id>/attachments/media/<int:attachment_id>', chat.views.delete_attachment, name='delete_image'),  # DELETE
    path('<int:chat_id>/attachments/contacts/<int:contact_id>/', chat.views.delete_contact, name='delete_contact'),  # DELETE
    path('<int:chat_id>/attachments/events/<int:event_id>/', chat.views.delete_event, name='delete_event'),  # DELETE
    path('<int:chat_id>/attachments/locations/<int:location_id>/', chat.views.delete_location, name='delete_location'),  # DELETE
]
