import requests
from django.shortcuts import get_object_or_404
from fcm_django.models import FCMDevice
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer
from utils.common import create_otp


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    if not request.method == 'POST':
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    phone = request.data['phone']
    otp = create_otp()

    user, created = User.objects.get_or_create(phone=phone)
    user.set_password(otp)
    user.save()

    send_message = requests.get(
        f'https://smsc.kz/sys/send.php?login=akzholqz&psw=01Cale02nda03ria&phones={phone}&mes=Код%20доступа%20Calendaria%20:%20{otp}'
    )

    if send_message.status_code == 200:
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def activate_user(request):
    if request.method == 'POST':
        if request.user:
            username = request.data['username']

            user = get_object_or_404(User, id=request.user.id)
            user.username = username
            user.is_active = True

            user.save()

            return Response({'message': 'User activated'}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def delete_user(request):
    User.objects.filter(id=request.user.id).delete()
    return Response({'message': 'user was deleted'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def logout(request):
    device_id = request.data['device_id']
    device = FCMDevice.objects.filter(registration_id=device_id).first()
    if device:
        device.delete()
    return Response({'message': 'User_logged out'}, status=status.HTTP_200_OK)
