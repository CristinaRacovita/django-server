from itertools import chain

import pandas as pd

from filmdb.models import Rating, TrainData
from utils.similarity import delete_users_from_ratings, get_most_similar_users


def get_movies_for_user_from_predictions(new_user, predictions):
    movies = {new_user: []}

    for row, index in predictions[predictions['user_id'] == new_user].iterrows():
        movies[new_user].append((row['movie_id_id'], row['rating']))

    return movies


def take__movie_ranks_for_all_ids(ids, count, movie_id):
    borda_number = 0
    for userId in ids:
        for i in range(len(count[userId])):
            if count[userId][i][0] == movie_id:
                borda_number += count[userId][i][1]
                break

    return borda_number


def get_movies_for_new_user(predictions_df, new_user, similar_users):
    movies = {new_user: []}

    movies_unique = predictions_df.movie_id_id.unique().tolist()

    data = delete_users_from_ratings(similar_users, predictions_df)

    for movie_id in movies_unique:
        movies[new_user].append((movie_id, data[data['movie_id_id'] == movie_id].rating.mean()))

    return movies


def concat_dicts(list_dicts):
    return dict(chain.from_iterable(d.items() for d in list_dicts))


def borda_count(users, user_movie, predictions, no_of_recommendations):
    all_dict = []

    train_data_for_similar = get_concat_train_data(user_movie)

    movies = get_movies_for_selected_users(all_dict, predictions, train_data_for_similar, users)

    for i in users:
        movies[i].sort(key=lambda tup: tup[1])

    count = {}
    for i in users:
        count[i] = []

    for userId in users:
        for i in range(len(movies[userId])):
            count[userId].append((movies[userId][i][0], i))

    movies_borda_count = []
    for movie_id in predictions.movie_id_id.unique():
        movies_borda_count.append((movie_id, take__movie_ranks_for_all_ids(users, count, movie_id)))

    movies_borda_count.sort(key=lambda tup: tup[1], reverse=True)

    if len(movies_borda_count) < no_of_recommendations:
        no_of_recommendations = len(movies_borda_count)

    recommendations = []

    for i in range(no_of_recommendations):
        recommendations.append(movies_borda_count[i][0])

    return recommendations


def get_movies_for_selected_users(all_dict, predictions, train_data_for_similar, users):
    for user in users:
        if predictions[predictions['user_id'] == user].empty:
            ids = get_most_similar_users(user, train_data_for_similar, 12, users)
            all_dict.append(get_movies_for_new_user(predictions, user, ids))
        else:
            all_dict.append(get_movies_for_user_from_predictions(users, predictions))
    movies = concat_dicts(all_dict)
    return movies


def get_concat_train_data(user_movie):
    train_data_df = pd.DataFrame(list(TrainData.objects.all().values()))
    res = {"user_id": [], "movie_id_id": [], "rating": [], "rating_id": []}
    for i in user_movie:
        res["user_id"].append(i.user_id.user_id)
        res["movie_id_id"].append(i.movie_id.movie_id)
        res["rating"].append(i.rating)
        res["rating_id"].append(None)
    user_data = pd.DataFrame(res, columns=['rating_id', 'user_id', 'movie_id_id', 'rating'])
    all_train_data = pd.concat([train_data_df, user_data], ignore_index=True, sort=True)
    train_data_for_similar = all_train_data.drop(columns=['rating_id'])
    return train_data_for_similar
