from django.conf.urls import url

from .views import credentials_list, train_data, get_movies, post_predictions, get_prediction, \
    get_movies_details, rate_movies, get_watched_movies, \
    add_description_ro, upload_image, image, get_users_details, check_credentials, add_group, add_members, \
    get_all_group, get_group_movie

urlpatterns = [
    url(r'^credentials$', credentials_list),
    url(r'^trainData$', train_data),
    url(r'^movies$', get_movies),
    url(r'^movies/details/(?P<ids>[\w\-]+)$', get_movies_details),
    url(r'^training$', post_predictions),
    url(r'^prediction/(?P<pk>[0-9]+)$', get_prediction),
    url(r'^rateMovies$', rate_movies),
    url(r'^watchedMovies/(?P<pk>[0-9]+)$', get_watched_movies),
    url(r'^updateDescriptionRo$', add_description_ro),
    url(r'^upload/(?P<pk>[0-9]+)$', upload_image),
    url(r'^image/(?P<pk>[0-9]+)$', image),
    url(r'^users/(?P<ids>[\w\-]+)$', get_users_details),
    url(r'^checkUser$', check_credentials),
    url(r'^createGroup$', add_group),
    url(r'^addMembers$', add_members),
    url(r'^group/(?P<pk>[0-9]+)$', get_all_group),
    url(r'^group/movies/(?P<group_id>[0-9]+)$', get_group_movie),
]
