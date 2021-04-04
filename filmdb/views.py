import itertools

import numpy as np
import pandas as pd
import tensorflow
from django.forms.models import model_to_dict
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from scipy.sparse import csr_matrix
from .matrix_factorizarion import build_sparse_tensor, MatrixFactorization, get_most_similar_user
from .models import User, TrainData, Movie, Prediction
from .serializers import UserSerializer, TrainDataSerializer, MovieSerializer
from .get_movies_details_from_web import get_image_url_and_synopsis_by_title


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
def get_movies(request):
    if request.method == 'GET':
        movie_serializer = MovieSerializer(Movie.objects.all(), many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)


@api_view(['POST'])
def post_movies(request):
    if request.method == 'POST':
        movies = JSONParser().parse(request)
        movie_serializer = MovieSerializer(data=movies, many=True)
        if movie_serializer.is_valid():
            movie_serializer.save()
            return JsonResponse(movie_serializer.data, status=status.HTTP_201_CREATED, safe=False)
        return JsonResponse(movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(['GET'])
def get_prediction(request, pk):
    training_data = TrainData.objects.all()
    res = []
    for i in training_data:
        res.append(model_to_dict(i))

    my_training_data = pd.DataFrame(res, columns=['rating_id', 'user_id', 'movie_id', 'rating'])
    my_training_data = my_training_data.drop(columns=['rating_id'])

    # my_training_data.user_id = my_training_data.user_id.astype('int')
    # print(my_training_data)
    sparse_train_data = csr_matrix((my_training_data.rating.values, (my_training_data.user_id.values,
                                                                     my_training_data.movie_id.values)))
    # print(sparse_train_data)
    most_similar_user_id = get_most_similar_user(pk, sparse_train_data)
    predictions = Prediction.objects.filter(user_id=most_similar_user_id)
    max_movie = predictions.order_by('-rating').first()

    # movie = Movie.objects.get(pk=max_movie.movie_id)

    # print(max_movie.movie_id.movie_title)
    return JsonResponse(max_movie.movie_id.movie_title, status=status.HTTP_201_CREATED,
                        safe=False)


@api_view(['GET'])
def get_predictions(request):
    if request.method == 'GET':
        Prediction.objects.all().delete()

        training_data = TrainData.objects.all()
        res = []
        for i in training_data:
            res.append(model_to_dict(i))

        my_training_data = pd.DataFrame(res, columns=['rating_id', 'user_id', 'movie_id', 'rating'])
        R = np.array(my_training_data.pivot(index='user_id', columns='movie_id', values='rating').fillna(0))
        indices = [[i, j] for i in range(R.shape[0]) for j in range(R.shape[1]) if R[i, j] > 0]
        shape = R.shape
        R = build_sparse_tensor(np.array(my_training_data.rating, dtype=np.float32), indices, shape)
        mf = MatrixFactorization(R, latent_features=20)
        mf.train(alpha=0.0003, iterations=50000, beta=0.0001)

        input = mf.full_matrix()
        output = tensorflow.where(input > 5, tensorflow.math.floor(input), input)
        ceil_predictions_matrix = tensorflow.math.ceil(output)

        print()
        print("P x Q:")
        print(ceil_predictions_matrix)
        print()

        predictions = ceil_predictions_matrix.numpy()

        shape_0 = predictions.shape[0]
        shape_1 = predictions.shape[1]

        indices = itertools.product(list(range(shape_0)), list(range(shape_1)))
        prediction_data = []

        table_pred = {"user_id": [], "movie_id": [], "rating": []}
        for [i, j] in indices:
            table_pred['user_id'].append(i + 1)
            table_pred['movie_id'].append(j + 1)
            table_pred['rating'].append(predictions[i][j])

        for index in range(len(table_pred['user_id'])):
            movie = Movie.objects.get(pk=table_pred["movie_id"][index])
            pred = Prediction(user_id=table_pred["user_id"][index], movie_id=movie,
                              rating=table_pred["rating"][index])
            prediction_data.append(pred)
            pred.save()

        return JsonResponse("Training is completed and predictions are saved.", status=status.HTTP_201_CREATED,
                            safe=False)


@api_view(['PUT'])
def update_image_url_and_description_for_movies(request):
    movies = Movie.objects.all()
    for movie in movies:
        if movie.movie_id != 243:
            image_url, synopsis = get_image_url_and_synopsis_by_title(movie.movie_title)
            movie.image_url = image_url
            movie.description = synopsis

        movie.save()
    return JsonResponse("Done.", status=status.HTTP_201_CREATED, safe=False)
