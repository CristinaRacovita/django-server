from django.db import models


class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    genre_value = models.CharField(max_length=30)

    class Meta:
        db_table = 'Genre'


class Movie(models.Model):
    movie_id = models.AutoField(primary_key=True)
    movie_title = models.CharField(max_length=50)
    release_date = models.CharField(max_length=30)

    class Meta:
        db_table = 'Movie'


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    gender = models.CharField(max_length=1)  # M or F
    age = models.IntegerField
    password = models.CharField(max_length=100)

    class Meta:
        db_table = 'User'


class MovieGenre(models.Model):
    movie_genre_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    genre_id = models.ForeignKey(Genre, on_delete=models.CASCADE, db_column='genre_id')

    class Meta:
        db_table = 'MovieGenre'
        unique_together = (('movie_id', 'genre_id'),)


class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    rating = models.FloatField

    class Meta:
        db_table = 'Rating'
        unique_together = (('movie_id', 'user_id'),)


class TrainData(models.Model):
    rating_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    rating = models.FloatField

    class Meta:
        db_table = 'TrainData'
        unique_together = (('movie_id', 'user_id'),)
