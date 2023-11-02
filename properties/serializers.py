from rest_framework import serializers
from properties.models import Timezone, Countrycode


class TimezoneSerializer(serializers.ModelSerializer):
    timezone = serializers.SerializerMethodField('timezone_set', read_only=True)

    def timezone_set(self, instance):
        timezone_name = f'{instance.name} {instance.value}'
        return timezone_name

    class Meta:
        model = Timezone
        fields = ['timezone']


class CountrycodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Countrycode
        fields = [
          'name',
          'dial_code',
          'code',
          'flag',
          ]
