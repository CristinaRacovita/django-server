from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from filmdb.models import GroupMovie, GroupUser
from filmdb.serializers import GroupMovieSerializer, DisplayMovieSerializer, UserDetailsSerializer, GroupUserSerializer, \
    GroupSerializer


@api_view(['POST'])
def add_group(request):
    if request.method == 'POST':
        group = JSONParser().parse(request)
        group_serializer = GroupSerializer(data=group)
        try:
            if group_serializer.is_valid():
                group_serializer.save()
                return JsonResponse(group_serializer.data, status=status.HTTP_201_CREATED, safe=False)
            return JsonResponse(group_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def add_members(request):
    if request.method == 'POST':
        group_user = JSONParser().parse(request)
        group_user_serializer = GroupUserSerializer(data=group_user, many=True)
        if group_user_serializer.is_valid():
            group_user_serializer.save()
            return JsonResponse(group_user_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(group_user_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(['GET'])
def get_all_group(request, pk):
    if request.method == 'GET':
        groups_users = GroupUser.objects.filter(user_id=int(pk))
        groups = []
        for group_user in groups_users:
            users_group = GroupUser.objects.filter(group_id=group_user.group_id.group_id)
            users = []
            for user in users_group:
                users.append(user.user_id)

            users_serializer = UserDetailsSerializer(users, many=True)

            groups.append({"group_id": group_user.group_id.group_id, "group_name": group_user.group_id.group_name,
                           "users": users_serializer.data})

        return JsonResponse(groups, status=status.HTTP_200_OK, safe=False)


@api_view(['GET'])
def get_group_movie(request, group_id):
    if request.method == 'GET':
        groups_users = GroupMovie.objects.filter(group_id=int(group_id))
        movies = []
        for group in groups_users:
            movies.append(group.movie_id)
        movie_serializer = DisplayMovieSerializer(movies, many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)


@api_view(['POST'])
def post_group_movie(request):
    if request.method == 'POST':
        group_movie = JSONParser().parse(request)
        group_movie_serializer = GroupMovieSerializer(data=group_movie)

        if group_movie_serializer.is_valid():
            group_movie_serializer.save()
            return JsonResponse(group_movie_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(group_movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
