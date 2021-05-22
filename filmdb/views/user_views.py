from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from filmdb.models import User
from filmdb.serializers import UserSerializer, UserDetailsSerializer, ProfileImageSerializer


@api_view(['POST', 'GET'])
def credentials_list(request):
    if request.method == 'POST':
        user_data = JSONParser().parse(request)

        users = User.objects.all()
        for user in users:
            if user.username == user_data['username']:
                return JsonResponse({"user_id": None, "username": None, "password": None},
                                    status=status.HTTP_201_CREATED)

        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        users_serializer = UserDetailsSerializer(User.objects.all(), many=True)
        return JsonResponse(users_serializer.data, status=status.HTTP_200_OK, safe=False)


@api_view(['POST'])
def check_credentials(request):
    if request.method == 'POST':
        user_data = JSONParser().parse(request)

        users = User.objects.all()
        for user in users:
            if user.username == user_data['username'] and user.password == user_data['password']:
                return JsonResponse({"user_id": user.user_id, "username": user.username}, status=status.HTTP_200_OK)

        return JsonResponse({"user_id": None, "username": None}, status=status.HTTP_200_OK)


@api_view(['POST'])
def upload_image(request, pk):
    if request.method == 'POST':
        user = User.objects.filter(user_id=int(pk))[0]
        try:
            user.profile_image = request.data['model_pic']
            user.save()

            return JsonResponse("Done.", status=status.HTTP_201_CREATED,
                                safe=False)
        except Exception as e:
            print(e.args[0])
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def image(request, pk):
    if request.method == 'GET':
        user = User.objects.filter(user_id=int(pk))[0]
        try:
            if user.profile_image:
                print(type(user.profile_image))
                dict_user = {"profile_image": user.profile_image}
                user_serializer = ProfileImageSerializer(data=dict_user)
                if user_serializer.is_valid():
                    return JsonResponse(user_serializer.data, status=status.HTTP_200_OK, safe=False)
                return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
            else:
                return JsonResponse({"profile_image": None}, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_users_details(request, ids):
    if request.method == 'GET':
        ids_str_arr = ids.split("-")

        ids_arr = []
        for movie_id in ids_str_arr:
            if movie_id != '':
                try:
                    int_id = int(movie_id)
                    ids_arr.append(int_id)
                except ValueError:
                    return JsonResponse("Not a int", status=status.HTTP_400_BAD_REQUEST, safe=False)

        users = []
        for user_id in ids_arr:
            user = User.objects.get(user_id=user_id)
            users.append(user)

        users_serializer = UserDetailsSerializer(users, many=True)

        return JsonResponse(users_serializer.data, status=status.HTTP_200_OK, safe=False)