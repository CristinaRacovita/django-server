from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from filmdb.models import Movie, Rating
from filmdb.serializers import MovieSerializer, WatchedMovieSerializer, RatingSerializer, DetailsMovieSerializer, \
    DisplayMovieSerializer
from filmdb.translation import translate_in_romanian


@api_view(['GET', 'POST'])
def get_movies(request):
    if request.method == 'GET':
        movie_serializer = MovieSerializer(Movie.objects.all(), many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)
    if request.method == 'POST':
        movies = JSONParser().parse(request)

        movie_serializer = MovieSerializer(data=movies, many=True)
        try:
            if movie_serializer.is_valid(raise_exception=True):
                movie_serializer.save()
                return JsonResponse(movie_serializer.data, status=status.HTTP_201_CREATED, safe=False)
            return JsonResponse(movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_movies_details(request, ids):
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

        movies = []
        for movie_id in ids_arr:
            movie = Movie.objects.get(movie_id=movie_id)
            movies.append(movie)

        movie_serializer = DetailsMovieSerializer(movies, many=True)

        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)


@api_view(['POST'])
def rate_movies(request):
    if request.method == 'POST':
        ratings = JSONParser().parse(request)
        rating_serializer = RatingSerializer(data=ratings, many=True)
        if rating_serializer.is_valid():
            rating_serializer.save()
            return JsonResponse(rating_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(rating_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(['GET'])
def get_watched_movies(request, pk):
    if request.method == 'GET':
        ratings = Rating.objects.filter(user_id=int(pk)).exclude(rating__isnull=True)
        watched_movies = []

        for r in ratings:
            watched_movies.append({"movie_title": r.movie_id.movie_title, "rating": r.rating})

        movie_serializer = WatchedMovieSerializer(data=watched_movies, many=True)
        try:
            if movie_serializer.is_valid():
                return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)
            return JsonResponse(movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def add_description_ro(request):
    if request.method == 'PUT':
        movies = Movie.objects.all()

        try:
            for movie in movies:
                if movie.description_ro is None and movie.movie_title:
                    print(movie.movie_title)
                    description_ro = translate_in_romanian(movie.description_en)
                    movie.description_ro = description_ro

                    movie.save()

        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            return JsonResponse("Done.", status=status.HTTP_201_CREATED,
                                safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_unrated_movies(request, pk):
    if request.method == 'GET':

        ratings = Rating.objects.filter(user_id=int(pk)).filter(rating__isnull=True).values("movie_id")
        ratings_null = []
        for rat in ratings:
            ratings_null.append(rat['movie_id'])
        movie_serializer = DisplayMovieSerializer(Movie.objects.filter(movie_id__in=ratings_null), many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)