from django.shortcuts import get_object_or_404
from fcm_django.models import FCMDevice
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer
from utils.common import create_otp


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def me_view(request):
    print('user: ', request.user)
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    phone = request.data['phone']

    user, created = User.objects.get_or_create(phone=phone)
    user.set_password('111111')
    user.save()

    return Response({'user_id': user.id}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def verify_user(request):
    user_id = request.data['user_id']
    code = request.data['code']

    user = get_object_or_404(User, id=user_id)

    if code == '111111':
        token, created = Token.objects.get_or_create(user=user)
        print('token', token.key, 'created', created)
        serializer = UserSerializer(user).data

        return Response(serializer, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def activate_user(request):
    if request.user:
        username = request.data['username']
        staff_secret = request.data.get('staff_secret', None)

        user = get_object_or_404(User, id=request.user.id)
        user.username = username
        user.is_registered = True

        if staff_secret == 'DiplomaWork':
            user.is_staff = True

        user.save()

        serializer = UserSerializer(user).data
        return Response(serializer, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
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
