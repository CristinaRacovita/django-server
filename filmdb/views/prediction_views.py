import itertools

from django.forms import model_to_dict
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from filmdb.models import TrainData, Rating, Prediction, Movie, MovieGenre
from filmdb.serializers import TrainDataSerializer
from utils.group_election import borda_count
import pandas as pd
import numpy as np

from utils.matrix_factorization import build_sparse_tensor, MatrixFactorization
from utils.similarity import get_best_movies_for_new_user, get_most_similar_users

NO_OF_SIMILAR_USERS = 12

NO_OF_MOVIES = 5


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

        print(ids_arr)

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
    mf = MatrixFactorization(R, latent_features=10)
    mf.train(alpha=0.005, iterations=50000, beta=0.0003)
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
