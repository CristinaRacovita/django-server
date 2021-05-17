import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


def get_most_similar_users(user_id, train_data, number, users=None):
    train_sparse_matrix = csr_matrix(
        (train_data.rating.values, (train_data.user_id.values, train_data.movie_id_id.values)))

    user_similarity = np.argsort(cosine_similarity(train_sparse_matrix[user_id], train_sparse_matrix).ravel())

    index = np.argwhere(user_similarity == user_id)
    user_similarity = np.delete(user_similarity, index)

    if users:
        for user_item in users:
            index = np.argwhere(user_similarity == user_item)
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
    movies_unique = predictions_df.movie_id_id.unique().tolist()

    data = delete_users_from_ratings(users_ids, predictions_df)

    for movieId in movies_unique:
        all_movies_average_rating.append((movieId, data[data['movie_id_id'] == movieId].rating.mean()))

    all_movies_average_rating.sort(key=take_second, reverse=True)
    recommendations = []

    if len(all_movies_average_rating) < number:
        number = len(all_movies_average_rating)

    for i in range(number):
        recommendations.append(all_movies_average_rating[i][0])

    return recommendations
