from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from properties.models import Timezone, Countrycode
from properties.serializers import TimezoneSerializer, CountrycodeSerializer


@api_view(['GET'])
@permission_classes((AllowAny,))
def timezone_list(request):
    if request.method == 'GET':
        timezones = Timezone.objects.all().order_by('id')
        timezones_list = []
        serializer = TimezoneSerializer(timezones, many=True)
        for timezone in serializer.data:
            timezones_list.append(timezone['timezone'])
        return Response(timezones_list, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny,))
def countrycodes_list(request):
    if request.method == 'GET':
        countrycodes = Countrycode.objects.all().order_by('id')
        serializer = CountrycodeSerializer(countrycodes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
