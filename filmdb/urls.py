from django.conf.urls import url

from .views import credentials_list, train_data

urlpatterns = [
    url(r'^credentials$', credentials_list),
    url(r'^trainData$', train_data)
]
