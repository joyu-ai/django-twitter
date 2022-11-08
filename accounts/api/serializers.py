from django.contrib.auth.models import User
from rest_framework import serializers, exceptions


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']


class UserSerializerForTweet(serializers.ModelSerializer): #不同的serializers满足不同的response的需求。
    class Meta:
        model = User
        fields = ['id', 'username']


class UserSerializerForLike(UserSerializerForTweet):
    pass


class UserSerializerForFriendship(UserSerializerForTweet): #不同的serializers满足不同的response的需求。
    pass


class UserSerializerForComment(UserSerializerForTweet): #不同的serializers满足不同的response的需求。
    pass


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        if not User.objects.filter(username=data['username'].lower()).exists():
            raise exceptions.ValidationError({
                'username': 'User does not exist.'
            })
        return data


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, min_length=6)
    password = serializers.CharField(max_length=20, min_length=6)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, data):
        if User.objects.filter(username=data['username'].lower()).exists():
            raise exceptions.ValidationError({
                'username': 'This username has been occupied.'
            })
        if User.objects.filter(email=data['email'].lower()).exists():
            raise exceptions.ValidationError({
                'email': "This email address has been occupied."
            })
        return data

    def create(self, validated_data):
        username = validated_data['username'].lower()
        email = validated_data['email'].lower()
        password = validated_data['password']
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.profile
        return user