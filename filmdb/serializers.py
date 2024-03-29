from rest_framework import serializers

from .models import User, TrainData, Movie, Rating, Group, GroupUser, GroupUserMovie, Genre, MovieGenre


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
        fields = ['movie_id', 'movie_title']
        extra_kwargs = {
            'image_url': {
                'required': False,
                'allow_blank': True,
            },
            'description_en': {
                'required': False,
                'allow_blank': True,
            },
            'description_ro': {
                'required': False,
                'allow_blank': True,
            }
        }


class DetailsMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('movie_id', 'movie_title', 'image_url')
        extra_kwargs = {
            'image_url': {
                'required': False,
                'allow_blank': True,
            }
        }


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'
        extra_kwargs = {
            'image_url': {
                'required': False,
                'allow_blank': True,
            },
            'description_en': {
                'required': False,
                'allow_blank': True,
            },
            'description_ro': {
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
        model = Rating
        fields = ('user_id', 'movie_id', 'rating',)


class WatchedMovieSerializer(serializers.Serializer):
    movie_title = serializers.CharField(max_length=200)
    rating = serializers.FloatField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('profile_image',)


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'username', 'profile_image')
        extra_kwargs = {
            'username': {
                'required': False,
                'allow_blank': True,
            }
        }


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class GroupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupUser
        fields = ('group_id', 'user_id', 'group_user_id')


class GroupMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupUserMovie
        fields = ('group_id', 'movie_id', 'group_movie_id')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class MovieGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieGenre
        fields = '__all__'
