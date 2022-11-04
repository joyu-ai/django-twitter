from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from rest_framework import serializers
from tweets.models import Tweet
from likes.services import LikeService
# 这个没有放在 api 里，因为这个共享代码不一定被 api 使用，也可能被异步任务使用
from likes.api.serializers import LikeSerializer


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet() # used in fields
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'has_liked',
        )

    def get_likes_count(self, obj):
        return obj.like_set.count()

    def get_comments_count(self, obj):
        return obj.comment_set.count()

    def get_has_liked(self, obj): # obj 得到这个帖子我有没有赞过
        return LikeService.has_liked(self.context['request'].user, obj)


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet


# 20.4 inject likes to api
# 改名，原来叫 TweetSerializerWithComments(
# 改继承，原来继承 serializers.ModelSerializer
class TweetSerializerForDetail(TweetSerializer):
    # user = UserSerializerForTweet()
    # <HOMEWORK> 使用 serialziers.SerializerMethodField 的方式实现 comments
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'comments',
            'created_at',
            'content',
            'likes',
            'comments',
            'likes_count',
            'comments_count',
            'has_liked',
            )