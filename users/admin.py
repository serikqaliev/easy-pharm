from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import (
    User
)
from django.contrib.auth.models import Group


# Админка пользователей
class UserCustomAdmin(UserAdmin):
    model = User
    list_display = (
        'username',
        'first_name',
        'last_name',
        'phone',
        'created_at',
    )
    list_filter = (
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
    )
    fieldsets = (
        ('Основное', {
            'fields': (
                'username',
                'first_name',
                'last_name',
                'phone',
                'avatar',
            )
        }),
    )


admin.site.register(User, UserCustomAdmin)
admin.site.unregister(Group)

# Настройки Хедеров в Админке
admin.site.site_header = 'Панель администратора'
admin.site.site_title = 'Админ-панель Calendaria'
admin.site.index_title = 'Админ-панель Calendaria'

