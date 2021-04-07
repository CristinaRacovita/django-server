from django.db import models


class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    genre_value = models.CharField(max_length=30)

    class Meta:
        db_table = 'Genre'


class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    movie_title = models.CharField(max_length=150)
    release_date = models.CharField(max_length=30)
    image_url = models.CharField(max_length=250, null=True)
    description = models.CharField(max_length=1000, null=True)

    class Meta:
        db_table = 'Movie'


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100,  db_column='username')
    password = models.CharField(max_length=100,  db_column='password')

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
    rating = models.FloatField()

    class Meta:
        db_table = 'Rating'
        unique_together = (('movie_id', 'user_id'),)


class TrainData(models.Model):
    rating_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    user_id = models.IntegerField()
    rating = models.IntegerField()

    class Meta:
        db_table = 'TrainData'
        unique_together = (('movie_id', 'user_id'),)


class Prediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    user_id = models.IntegerField()
    rating = models.IntegerField()

    class Meta:
        db_table = 'Prediction'
        unique_together = (('movie_id', 'user_id'),)


class RatingMovieUser(models.Model):
    rating_id = models.AutoField(primary_key=True)
    movie_id = models.ForeignKey(Movie, on_delete=models.CASCADE, db_column='movie_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    rating = models.FloatField()

    class Meta:
        db_table = 'RatingUserMovie'
        unique_together = (('movie_id', 'user_id'),)