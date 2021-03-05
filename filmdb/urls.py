from django.conf.urls import url

from .views import credentials_list

urlpatterns = [
    url(r'^credentials$', credentials_list),
]