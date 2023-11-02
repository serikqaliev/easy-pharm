from django.contrib import admin

from notifications.models import Notification


class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = ('notification_title', 'notification_type', 'text')
    search_fields = ('notification_title',)


admin.site.register(Notification, NotificationAdmin)


# Register your models here.
