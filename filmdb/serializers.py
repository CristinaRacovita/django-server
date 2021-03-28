from rest_framework import serializers

from .models import User, TrainData


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'username', 'password',)


class TrainDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainData
        fields = ('user_id', 'movie_id', 'rating')
