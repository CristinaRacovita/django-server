from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from .models import User, TrainData
from .serializers import UserSerializer, TrainDataSerializer


@api_view(['GET', 'POST', 'DELETE'])
def credentials_list(request):
    if request.method == 'GET':
        users_serializer = UserSerializer(User.objects.all(), many=True)
        return JsonResponse(users_serializer.data, status=status.HTTP_200_OK, safe=False)

    elif request.method == 'POST':
        user_data = JSONParser().parse(request)
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def train_data(request):
    if request.method == 'GET':
        train_data_serializer = TrainDataSerializer(TrainData.objects.all(), many=True)
        return JsonResponse(train_data_serializer.data, status=status.HTTP_200_OK, safe=False)
