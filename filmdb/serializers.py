from rest_framework import serializers

from .models import User, TrainData, Movie, Rating, RatingMovieUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'username', 'password')
        extra_kwargs = {
            'username': {
                'required': False,
                'allow_blank': True,
            },
            'password': {
                'required': False,
                'allow_blank': True,
            }
        }


class TrainDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainData
        fields = ('rating_id', 'user_id', 'movie_id', 'rating',)


class DisplayMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('movie_id', 'movie_title')
        extra_kwargs = {
            'release_date': {
                'required': False,
                'allow_blank': True,
            }
        }


class DetailsMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('movie_id', 'movie_title', 'image_url')
        extra_kwargs = {
            'release_date': {
                'required': False,
                'allow_blank': True,
            },
            'image_url': {
                'required': False,
                'allow_blank': True,
            }
        }


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainData
        fields = ('prediction_id', 'user_id', 'movie_id', 'rating',)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatingMovieUser
        fields = ('user_id', 'movie_id', 'rating',)
