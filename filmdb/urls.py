from django.conf.urls import url

from filmdb.views.genre_views import post_genres, post_movies_genres
from filmdb.views.group_views import add_group, add_members, get_all_group, get_group_movie, post_group_movie
from filmdb.views.movie_views import get_movies, get_movies_details, rate_movies, get_watched_movies, \
    get_unrated_movies
from filmdb.views.prediction_views import train_data, post_predictions, get_prediction, get_group_prediction
from filmdb.views.user_views import credentials_list, upload_image, image, get_users_details, check_credentials

urlpatterns = [
    url(r'^credentials$', credentials_list),
    url(r'^trainData$', train_data),
    url(r'^movies$', get_movies),
    url(r'^movies/details/(?P<ids>[\w\-]+)$', get_movies_details),
    url(r'^training$', post_predictions),
    url(r'^prediction/(?P<pk>[0-9]+)$', get_prediction),
    url(r'^rateMovies$', rate_movies),
    url(r'^watchedMovies/(?P<pk>[0-9]+)$', get_watched_movies),
    url(r'^upload/(?P<pk>[0-9]+)$', upload_image),
    url(r'^image/(?P<pk>[0-9]+)$', image),
    url(r'^users/(?P<ids>[\w\-]+)$', get_users_details),
    url(r'^checkUser$', check_credentials),
    url(r'^createGroup$', add_group),
    url(r'^addMembers$', add_members),
    url(r'^group/(?P<pk>[0-9]+)$', get_all_group),
    url(r'^group/movies/(?P<group_id>[0-9]+)$', get_group_movie),
    url(r'^genres$', post_genres),
    url(r'^moviesGenres$', post_movies_genres),
    url(r'^group/recommendation/(?P<ids>[\w\-]+)$', get_group_prediction),
    url(r'^unrated/(?P<pk>[0-9]+)$', get_unrated_movies),
    url(r'^groupMovies$', post_group_movie),
]
