import itertools

import numpy as np
import pandas as pd
from django.forms.models import model_to_dict
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from utils.group_election import borda_count
from utils.matrix_factorizarion import build_sparse_tensor, MatrixFactorization
from utils.similarity import get_most_similar_users, get_best_movies_for_new_user
from .models import User, TrainData, Movie, Prediction, Rating, GroupUser, GroupUserMovie, MovieGenre
from .serializers import TrainDataSerializer, DetailsMovieSerializer, \
    RatingSerializer, UserSerializer, WatchedMovieSerializer, ProfileImageSerializer, UserDetailsSerializer, \
    GroupSerializer, GroupUserSerializer, GroupMovieSerializer, MovieSerializer, GenreSerializer, MovieGenreSerializer, \
    DisplayMovieSerializer
from .translation import translate_in_romanian

NO_OF_SIMILAR_USERS = 12

NO_OF_MOVIES = 5


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


@api_view(['GET', 'POST'])
def train_data(request):
    if request.method == 'GET':
        train_data_serializer = TrainDataSerializer(TrainData.objects.all(), many=True)
        return JsonResponse(train_data_serializer.data, status=status.HTTP_200_OK, safe=False)
    elif request.method == 'POST':
        TrainData.objects.all().delete()
        train_data_request = JSONParser().parse(request)
        train_serializer = TrainDataSerializer(data=train_data_request, many=True)
        if train_serializer.is_valid():
            train_serializer.save()
            return JsonResponse(train_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(train_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)


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
            print("BAD")
            return JsonResponse(movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_group_prediction(request, ids):
    if request.method == 'GET':
        ids_str_arr = ids.split("-")

        ids_arr = []
        for user_id in ids_str_arr:
            if user_id != '':
                try:
                    int_id = int(user_id)
                    ids_arr.append(int_id)
                except ValueError:
                    return JsonResponse("Not a int", status=status.HTTP_400_BAD_REQUEST, safe=False)

        user_movie = Rating.objects.filter(user_id__in=ids_arr)
        ratings = list(user_movie.select_related('movie_id').values('movie_id__movie_id'))

        watched_movies = []
        for movie in ratings:
            watched_movies.append(movie['movie_id__movie_id'])

        predictions_df = pd.DataFrame(list(Prediction.objects.all().select_related('movie_id').exclude(
            movie_id__movie_id__in=watched_movies).values()))

        movies = borda_count(ids_arr, user_movie.exclude(rating__isnull=True), predictions_df, NO_OF_MOVIES)
        movies_dict = []
        for movie_id in movies:
            movie = Movie.objects.get(pk=movie_id)
            movies_dict.append(model_to_dict(movie))

        try:
            return JsonResponse(movies_dict, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_prediction(request, pk):
    genre = request.GET.get('genre', '')
    year = request.GET.get('year', '')
    print(genre + " " + year + "\n")

    predictions_df = get_predictions(genre, year, pk)

    if predictions_df[predictions_df['user_id'] == int(pk)].empty:
        most_similar_users = get_similar_user(pk)
    else:
        most_similar_users = [int(pk)]

    max_prediction_ids = get_best_movies_for_new_user(predictions_df, most_similar_users, NO_OF_MOVIES)
    movies = []

    for movie_id in max_prediction_ids:
        movie = Movie.objects.get(pk=movie_id)
        movies.append(model_to_dict(movie))

    try:
        return JsonResponse(movies, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


def get_predictions(genre, year, pk):
    ratings = list(Rating.objects.filter(user_id=int(pk)).select_related('movie_id').values('movie_id__movie_id'))

    watched_movies = []
    for movie in ratings:
        watched_movies.append(movie['movie_id__movie_id'])

    if genre != '' or year != '':
        if genre != '':
            movie_genre = list(MovieGenre.objects.all().select_related('genre_id', 'movie_id').filter(
                genre_id__genre_value=genre).exclude(movie_id__movie_id__in=watched_movies).values(
                'movie_id__movie_id'))
            selected_movies = []
            for movie in movie_genre:
                selected_movies.append(movie['movie_id__movie_id'])

        if genre != '' and year != '':
            year = int(year)
            predictions = pd.DataFrame(list(
                Prediction.objects.all().select_related('movie_id').filter(movie_id__release_year__gte=year).filter(
                    movie_id__movie_id__in=selected_movies).exclude(movie_id__movie_id__in=watched_movies).values()))
        elif genre != '':
            predictions = pd.DataFrame(list(
                Prediction.objects.all().select_related('movie_id').filter(
                    movie_id__movie_id__in=selected_movies).exclude(movie_id__movie_id__in=watched_movies).values()))
        elif year != '':
            year = int(year)
            predictions = pd.DataFrame(list(
                Prediction.objects.all().select_related('movie_id').filter(movie_id__release_year__gte=year).exclude(
                    movie_id__movie_id__in=watched_movies).values()))

    else:
        predictions = pd.DataFrame(
            list(Prediction.objects.all().exclude(movie_id__movie_id__in=watched_movies).values()))

    return predictions


def get_similar_user(pk):
    user_movie = Rating.objects.filter(user_id=int(pk)).exclude(rating__isnull=True)

    train_data_df = pd.DataFrame(list(TrainData.objects.all().values()))

    res = {"user_id": [], "movie_id_id": [], "rating": [], "rating_id": []}

    for i in user_movie:
        res["user_id"].append(int(pk))
        res["movie_id_id"].append(i.movie_id.movie_id)
        res["rating"].append(i.rating)
        res["rating_id"].append(None)

    user_data = pd.DataFrame(res, columns=['rating_id', 'user_id', 'movie_id_id', 'rating'])

    all_train_data = pd.concat([train_data_df, user_data], ignore_index=True, sort=True)
    all_train_data = all_train_data.drop(columns=['rating_id'])

    most_similar_users = get_most_similar_users(int(pk), all_train_data, NO_OF_SIMILAR_USERS)

    return most_similar_users


@api_view(['POST'])
def post_predictions(request):
    if request.method == 'POST':
        Prediction.objects.all().delete()

        training_data = TrainData.objects.all()
        my_training_data = get_df_from_models(training_data, ['rating_id', 'user_id', 'movie_id', 'rating'])
        del my_training_data['rating_id']

        print(my_training_data)

        ratings = Rating.objects.all().exclude(rating__isnull=True)
        ratings_data = get_df_from_models(ratings, ['user_id', 'movie_id', 'rating'])
        all_data = pd.concat([my_training_data, ratings_data], ignore_index=True, sort=True)

        predictions = training_process(all_data)

        prediction_data, table_pred = process_data_for_prediction_table(all_data, predictions)

        for index in range(len(table_pred['user_id'])):
            movie = Movie.objects.get(pk=table_pred["movie_id"][index])
            pred = Prediction(user_id=table_pred["user_id"][index], movie_id=movie,
                              rating=table_pred["rating"][index])
            prediction_data.append(pred)
            pred.save()

        return JsonResponse("Training is completed and predictions are saved.", status=status.HTTP_201_CREATED,
                            safe=False)


def process_data_for_prediction_table(all_data, predictions):
    shape_0 = predictions.shape[0]
    shape_1 = predictions.shape[1]
    indices = itertools.product(list(range(shape_0)), list(range(shape_1)))
    prediction_data = []
    movies_index = all_data.movie_id.unique()
    table_pred = {"user_id": [], "movie_id": [], "rating": []}
    for [i, j] in indices:
        table_pred['user_id'].append(i + 1)
        table_pred['movie_id'].append(movies_index[j])
        table_pred['rating'].append(round(predictions[i][j], 2))
    return prediction_data, table_pred


def training_process(data):
    R = np.array(data.pivot(index='user_id', columns='movie_id', values='rating').fillna(0))
    indices = [[i, j] for i in range(R.shape[0]) for j in range(R.shape[1]) if R[i, j] > 0]
    shape = R.shape
    R = build_sparse_tensor(np.array(data.rating, dtype=np.float32), indices, shape)
    mf = MatrixFactorization(R, latent_features=20)
    mf.train(alpha=0.0003, iterations=50000, beta=0.0001)
    print()
    print("P x Q:")
    print(mf.full_matrix())
    print()
    predictions = mf.full_matrix().numpy()
    return predictions


def get_df_from_models(data, columns):
    res = []
    for i in data:
        res.append(model_to_dict(i))
    return pd.DataFrame(res, columns=columns)


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
        groups_users = GroupUserMovie.objects.filter(group_id=int(group_id))
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


@api_view(['GET'])
def get_unrated_movies(request, pk):
    if request.method == 'GET':

        ratings = Rating.objects.filter(user_id=int(pk)).filter(rating__isnull=True).values("movie_id")
        ratings_null = []
        for rat in ratings:
            ratings_null.append(rat['movie_id'])
        movie_serializer = DisplayMovieSerializer(Movie.objects.filter(movie_id__in=ratings_null), many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)


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
