from django.conf.urls import url

from .views import credentials_list, train_data, get_movies, post_predictions, get_prediction, \
    update_image_url_and_description_for_movies, get_movies_details, rate_movies, get_watched_movies, \
    add_description_ro, upload_image, image

urlpatterns = [
    url(r'^credentials$', credentials_list),
    url(r'^trainData$', train_data),
    url(r'^movies$', get_movies),
    url(r'^movies/details/(?P<ids>[\w\-]+)$', get_movies_details),
    url(r'^training$', post_predictions),
    url(r'^prediction/(?P<pk>[0-9]+)$', get_prediction),
    url(r'^image$', update_image_url_and_description_for_movies),
    url(r'^rateMovies$', rate_movies),
    url(r'^watchedMovies/(?P<pk>[0-9]+)$', get_watched_movies),
    url(r'^updateDescriptionRo$', add_description_ro),
    url(r'^upload/(?P<pk>[0-9]+)$', upload_image),
    url(r'^image/(?P<pk>[0-9]+)$', image),

]
