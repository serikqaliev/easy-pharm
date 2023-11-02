from django.contrib import admin
from properties.models import Timezone, Countrycode


class TimezoneAdmin(admin.ModelAdmin):
    model = Timezone
    list_display = ('name', 'value')
    search_fields = ('name',)


class CountrycodeAdmin(admin.ModelAdmin):
    model = Countrycode
    list_display = ('name', 'dial_code')
    search_fields = ('name',)


admin.site.register(Timezone, TimezoneAdmin)
admin.site.register(Countrycode, CountrycodeAdmin)

# Register your models here.
