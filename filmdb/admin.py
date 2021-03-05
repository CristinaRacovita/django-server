from django.contrib import admin

# Register your models here.
from .models import User, Movie, Genre, MovieGenre, Rating

admin.site.register(User)
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(MovieGenre)
admin.site.register(Rating)