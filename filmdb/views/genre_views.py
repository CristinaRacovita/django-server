from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from filmdb.serializers import GenreSerializer, MovieGenreSerializer


@api_view(['POST'])
def post_genres(request):
    if request.method == 'POST':
        genres = JSONParser().parse(request)
        genres_serializer = GenreSerializer(data=genres, many=True)

        if genres_serializer.is_valid():
            genres_serializer.save()
            return JsonResponse(genres_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(genres_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(['POST'])
def post_movies_genres(request):
    if request.method == 'POST':
        movies_genres = JSONParser().parse(request)
        movies_genres_serializer = MovieGenreSerializer(data=movies_genres, many=True)

        if movies_genres_serializer.is_valid():
            movies_genres_serializer.save()
            return JsonResponse(movies_genres_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(movies_genres_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
