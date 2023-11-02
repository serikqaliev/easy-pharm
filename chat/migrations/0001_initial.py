# Generated by Django 4.2.4 on 2023-10-17 05:03

import datetime
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment_type', models.CharField(choices=[('IMAGE', 'IMAGE'), ('VIDEO', 'VIDEO'), ('FILE', 'FILE')], max_length=256, verbose_name='Type of attachment')),
                ('file', models.FileField(blank=True, null=True, upload_to='chat/attachments', verbose_name='File')),
                ('size', models.IntegerField(blank=True, null=True, verbose_name='Size of attachment in bytes')),
                ('duration', models.IntegerField(blank=True, null=True, verbose_name='Duration of attachment in seconds (for video)')),
                ('width', models.IntegerField(blank=True, null=True, verbose_name='Width of attachment in pixels (for image, video)')),
                ('height', models.IntegerField(blank=True, null=True, verbose_name='Height of attachment in pixels (for image, video)')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_type', models.CharField(choices=[('direct', 'direct'), ('group', 'group'), ('event', 'event')], max_length=256, verbose_name='Type of chat')),
                ('title', models.CharField(blank=True, help_text='For direct chat - null, for group chat - title of group, for event chat - null (title of event)', max_length=256, null=True, verbose_name='Title of chat')),
                ('description', models.CharField(blank=True, help_text='For direct chat - null, for group chat - description of group, for event chat - null (description of event)', max_length=900, null=True, verbose_name='Description of chat')),
                ('cover_image', models.ImageField(blank=True, help_text='For direct chat - null, for group chat - cover image of group, for event chat - null (cover image of event)', null=True, upload_to='chat/covers', verbose_name='Cover image')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
            ],
            options={
                'verbose_name': 'Chat',
                'verbose_name_plural': 'Chats',
            },
        ),
        migrations.CreateModel(
            name='ContactMessageAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
            ],
            options={
                'verbose_name': 'Contact attachment',
                'verbose_name_plural': 'Contact attachments',
            },
        ),
        migrations.CreateModel(
            name='DeletedChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Deleted at')),
            ],
            options={
                'verbose_name': 'Deleted chat',
                'verbose_name_plural': 'Deleted chats',
            },
        ),
        migrations.CreateModel(
            name='DeletedMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Дата удаления')),
            ],
            options={
                'verbose_name': 'Удаленное сообщение',
                'verbose_name_plural': 'Удаленные сообщения',
            },
        ),
        migrations.CreateModel(
            name='EventMessageAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
            ],
            options={
                'verbose_name': 'Event attachment',
                'verbose_name_plural': 'Event attachments',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(blank=True, max_length=5120, null=True, verbose_name='URL')),
            ],
            options={
                'verbose_name': 'Link',
                'verbose_name_plural': 'Links',
            },
        ),
        migrations.CreateModel(
            name='LocationMessageAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='Latitude')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='Longitude')),
                ('address', models.CharField(blank=True, default='', max_length=256, verbose_name='Address')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
            ],
            options={
                'verbose_name': 'Location attachment',
                'verbose_name_plural': 'Location attachments',
            },
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, choices=[('Owner', 'Owner'), ('Admin', 'Admin'), ('Participant', 'Participant')], max_length=256, verbose_name='Member type')),
                ('status', models.CharField(blank=True, choices=[('Active', 'Active'), ('Kicked', 'Kicked'), ('Left', 'Left')], default='Active', max_length=256, verbose_name='Member status')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('muted_at', models.DateTimeField(blank=True, help_text='If not null this user muted this chat', null=True, verbose_name='Muted at')),
                ('kicked_at', models.DateTimeField(blank=True, null=True, verbose_name='Kicked at')),
                ('left_at', models.DateTimeField(blank=True, null=True, verbose_name='Left at')),
                ('archived_at', models.DateTimeField(blank=True, null=True, verbose_name='Archived at')),
                ('pinned_at', models.DateTimeField(blank=True, null=True, verbose_name='Pinned at')),
                ('truncated_at', models.DateTimeField(blank=True, null=True, verbose_name='Truncated at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
                ('last_read_at', models.DateTimeField(blank=True, default=datetime.datetime.now, null=True, verbose_name='Last read at')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.chat', verbose_name='Chat')),
            ],
            options={
                'verbose_name': 'Member',
                'verbose_name_plural': 'Members',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=256, verbose_name='UUID of message')),
                ('type', models.CharField(blank=True, choices=[('system', 'system'), ('regular', 'regular')], default='regular', max_length=256, null=True, verbose_name='Message type')),
                ('text', models.CharField(blank=True, max_length=5120, null=True, verbose_name='Text')),
                ('pinned_at', models.DateTimeField(blank=True, default=None, null=True, verbose_name='Pinned at')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Updated at')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted at')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.chat', verbose_name='Chat')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.contactmessageattachment', verbose_name='Contact')),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.eventmessageattachment', verbose_name='Event')),
                ('pinned_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pinned_by', to='chat.member', verbose_name='Pinned by')),
                ('replay_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.message', verbose_name='Replay to')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.member', verbose_name='Member')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
            },
        ),
        migrations.CreateModel(
            name='SystemMessageAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(blank=True, choices=[('chat.new', 'chat.new'), ('chat.title_changed', 'chat.title_changed'), ('chat.description_changed', 'chat.description_changed'), ('chat.cover_changed', 'chat.cover_changed'), ('member.joined', 'member.joined'), ('member.added', 'member.added'), ('member.left', 'member.left'), ('member.kicked', 'member.kicked'), ('member.role_changed', 'member.role_changed'), ('message.pinned', 'message.pinned'), ('message.unpinned', 'message.unpinned')], max_length=256, null=True, verbose_name='Action type')),
                ('changed_from', models.CharField(blank=True, max_length=900, null=True, verbose_name='Changed from')),
                ('changed_to', models.CharField(blank=True, max_length=900, null=True, verbose_name='Changed to')),
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='chat.message', verbose_name='Message')),
                ('target', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_of_system_message', to='chat.member', verbose_name='Target member')),
                ('target_chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_chat_of_system_message', to='chat.chat', verbose_name='Target chat')),
                ('target_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_message_of_system_message', to='chat.message', verbose_name='Target message')),
            ],
            options={
                'verbose_name': 'System message action',
                'verbose_name_plural': 'System message actions',
            },
        ),
        migrations.AddField(
            model_name='member',
            name='last_message',
            field=models.ForeignKey(blank=True, help_text='Last message which user can access (not deleted for all, not deleted for user)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='member_last_message', to='chat.message', verbose_name='Last message'),
        ),
    ]
