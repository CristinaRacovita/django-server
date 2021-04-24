import itertools

import numpy as np
import pandas as pd
from django.forms.models import model_to_dict
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from scipy.sparse import csr_matrix

from .get_movies_details_from_web import get_image_url_and_synopsis_by_title
from .matrix_factorizarion import build_sparse_tensor, MatrixFactorization, get_most_similar_user
from .models import User, TrainData, Movie, Prediction, Rating
from .serializers import TrainDataSerializer, DisplayMovieSerializer, DetailsMovieSerializer, \
    RatingSerializer, UserSerializer, WatchedMovieSerializer, ProfileImageSerializer
from .translation import translate_in_romanian


@api_view(['GET', 'POST'])
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


@api_view(['GET', 'POST'])
def get_movies(request):
    if request.method == 'GET':
        movie_serializer = DisplayMovieSerializer(Movie.objects.all(), many=True)
        return JsonResponse(movie_serializer.data, status=status.HTTP_200_OK, safe=False)
    if request.method == 'POST':
        movies = JSONParser().parse(request)

        movie_serializer = DisplayMovieSerializer(data=movies, many=True)
        try:
            if movie_serializer.is_valid(raise_exception=True):
                movie_serializer.save()
                return JsonResponse(movie_serializer.data, status=status.HTTP_201_CREATED, safe=False)
            print("BAD")
            return JsonResponse(movie_serializer.errors, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except Exception as e:
            return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_prediction(request, pk):
    user_movie = Rating.objects.filter(user_id=int(pk))

    training_data = TrainData.objects.all()
    res = []
    for i in training_data:
        res.append(model_to_dict(i))

    max_user_id = training_data.order_by('-user_id').first()

    new_user_id = max_user_id.user_id + 1

    j = 1100000
    for i in user_movie:
        train_data_obj = TrainData(user_id=new_user_id, movie_id=i.movie_id, rating=int(i.rating), rating_id=j + 1)
        res.append(model_to_dict(train_data_obj))

    my_training_data = pd.DataFrame(res, columns=['rating_id', 'user_id', 'movie_id', 'rating'])
    my_training_data = my_training_data.drop(columns=['rating_id'])
    sparse_train_data = csr_matrix((my_training_data.rating.values, (my_training_data.user_id.values,
                                                                     my_training_data.movie_id.values)))
    # print(sparse_train_data)

    most_similar_user_id = get_most_similar_user(new_user_id, sparse_train_data)
    # print(most_similar_user_id)
    predictions = Prediction.objects.filter(user_id=most_similar_user_id)

    max_prediction = predictions.order_by('-rating')[0:10]
    movies = []

    for m in max_prediction:
        movies.append(model_to_dict(m.movie_id))

    try:
        return JsonResponse(movies, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse({'error': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def post_predictions(request):
    if request.method == 'POST':
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

        # input = mf.full_matrix()
        # output = tensorflow.where(input > 5, tensorflow.math.floor(input), input)
        # ceil_predictions_matrix = tensorflow.math.ceil(output)

        print()
        print("P x Q:")
        print(mf.full_matrix())
        print()

        predictions = mf.full_matrix().numpy()

        shape_0 = predictions.shape[0]
        shape_1 = predictions.shape[1]

        indices = itertools.product(list(range(shape_0)), list(range(shape_1)))
        prediction_data = []

        movies_index = my_training_data.movie_id.unique()

        table_pred = {"user_id": [], "movie_id": [], "rating": []}
        for [i, j] in indices:
            table_pred['user_id'].append(i + 1)
            table_pred['movie_id'].append(movies_index[j])
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
    if request.method == 'PUT':
        movies = Movie.objects.all()
        for movie in movies:
            image_url, synopsis = get_image_url_and_synopsis_by_title(movie.movie_title)
            movie.image_url = image_url
            movie.description_en = synopsis

            movie.save()
        return JsonResponse("Done.", status=status.HTTP_201_CREATED, safe=False)


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
        ratings = Rating.objects.filter(user_id=int(pk))
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
        print("I am here")
        user = User.objects.filter(user_id=int(pk))[0]
        print("I am here")
        print(request.data['model_pic'])

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
