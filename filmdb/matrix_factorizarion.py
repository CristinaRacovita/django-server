import numpy as np
import tensorflow as tf
from numpy.ma import indices
from sklearn.metrics.pairwise import cosine_similarity


def build_sparse_tensor(np_array, indices, shape):
    return tf.SparseTensor(
        indices=indices,
        values=np_array,
        dense_shape=[shape[0], shape[1]])


def get_most_similar_user(user_id, train_sparse_matrix):
    int_id = int(user_id)
    user_similarity = np.argsort(cosine_similarity(train_sparse_matrix[int_id], train_sparse_matrix).ravel())
    length_sim = user_similarity.size
    return user_similarity[length_sim - 2]


class MatrixFactorization:
    def __init__(self, data, latent_features):
        self.latent_features = latent_features
        self.num_users, self.num_items = data.dense_shape
        self.Q = tf.Variable(tf.random.normal(shape=[self.latent_features, self.num_items]),
                             dtype=tf.float32, trainable=True)
        self.P = tf.Variable(tf.random.normal(shape=[self.num_users, self.latent_features]),
                             dtype=tf.float32, trainable=True)
        self.data = data

    def train(self, alpha, iterations, beta):
        optimizer = tf.optimizers.Adam(alpha)

        nr_validation = 10

        loss_hist = np.zeros(nr_validation, np.float32)

        for i in range(iterations):
            loss_mse = lambda: tf.reduce_sum(tf.losses.mean_squared_error(self.data.values,
                                                                          tf.gather_nd(tf.matmul(self.P, self.Q),
                                                                                       self.data.indices))) + \
                               self.regularization(beta)

            optimizer.minimize(loss_mse, var_list=[self.P, self.Q])

            mse = loss_mse()
            loss_hist[i % nr_validation] = mse
            if i % nr_validation == 0 and i != 0:
                if loss_hist[nr_validation - 1] - loss_hist[1] >= 0:
                    print(i)
                    print(32 * "-")
                    print(loss_hist)
                    break

            if (i + 1) % 25 == 0:
                print("Iteration: %d ; error = %.4f; " % (i + 1, mse))

    def regularization(self, beta):
        pow_P = tf.pow(self.P, 2)
        pow_Q = tf.pow(self.Q, 2)
        sum_P = tf.reduce_sum(pow_P)
        sum_Q = tf.reduce_sum(pow_Q)

        return (sum_Q + sum_P) * beta

    def full_matrix(self):
        return tf.matmul(self.P, self.Q)

    def get_predictions(self, user_id, movie_id):
        return tf.gather_nd(self.full_matrix(), [user_id, movie_id])
