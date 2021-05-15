from turtle import pd

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def get_most_similar_users(user_data, train_data, number):
    userId = user_data['user_id'].tolist()[0]
    all_data = pd.concat([train_data, user_data], ignore_index=True, sort=True)
    train_sparse_matrix = csr_matrix((all_data.rating.values, (all_data.user_id.values, all_data.movie_id.values)))

    user_similarity = np.argsort(cosine_similarity(train_sparse_matrix[userId], train_sparse_matrix).ravel())

    index = np.argwhere(user_similarity == userId)
    user_similarity = np.delete(user_similarity, index)

    length_sim = user_similarity.size
    top_sim_users = []
    for i in range(number):
        top_sim_users.append(user_similarity[length_sim - i - 1])

    return top_sim_users


def contains(user_id, ids):
    for id_item in ids:
        if id_item == user_id:
            return True

    return False


def delete_users_from_ratings(ids, ratings):
    data = ratings
    data['filterCols'] = data.user_id.apply(lambda user_id: contains(user_id, ids))
    data = data[data['filterCols']]
    del data['filterCols']

    return data


def take_second(elem):
    return elem[1]


def get_best_movies_for_new_user(predictions_df, users_ids, number):
    all_movies_average_rating = []
    movies_unique = predictions_df.movie_id.unique().tolist()

    data = delete_users_from_ratings(users_ids, predictions_df)

    for movieId in movies_unique:
        all_movies_average_rating.append((movieId, data[data['movie_id'] == movieId].rating.mean()))

    all_movies_average_rating.sort(key=take_second, reverse=True)
    recommendations = []

    for i in range(number):
        recommendations.append(all_movies_average_rating[i])

    return recommendations
