from rest_framework import serializers

from .models import User, TrainData, Movie


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'username', 'password',)


class TrainDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainData
        fields = ('rating_id', 'user_id', 'movie_id', 'rating',)


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('movie_id', 'movie_title', 'release_date')
        extra_kwargs = {
            'release_date': {
                'required': False,
                'allow_blank': True,
            }
        }


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainData
        fields = ('prediction_id', 'user_id', 'movie_id', 'rating',)
