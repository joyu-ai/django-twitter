from newsfeeds.services import NewsFeedService
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from tweets.api.serializers import (
    TweetSerializer,
    TweetSerializerForCreate,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_params
from utils.paginations import EndlessPagination


class TweetViewSet(GenericViewSet):
    """
    API endpoint that allows users to create, list tweets
    """
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:  # self.action 指调用的带request的函数
            return [AllowAny()]
        return [IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        # <HOMEWORK 1> 通过某个 query 参数 with_all_comments 来决定是否需要带上所有 comments
        # <HOMEWORK 2> 通过某个 query 参数 with_preview_comments 来决定是否需要带上前三条 comments
        tweet = self.get_object()
        # return Response(
        #     TweetSerializerForDetail(tweet, context={'request': request}).data,
        # ) # 20.4 因为继承了 TweetSerializer 也要传 context
        serializer = TweetSerializerForDetail(
            tweet,
            context={'request': request},
        )
        return Response(serializer.data)

    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs): # 只有加了view function，才会在api root页面看到链接。
        """
        重载 list方法，不列出所有 tweets，必须要求指定 user_id 作为筛选条件。
        """
        user_id = request.query_params['user_id']
        tweets = TweetService.get_cached_tweets(user_id=user_id)
        tweets = self.paginate_queryset(tweets)
        serializer = TweetSerializer(
            tweets,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    def create(self, request):
        """
        重载 create 方法，因为需要默认用当前登录用户作为 tweet.user。
        """
        serializer = TweetSerializerForCreate( # 创建用的一个serializer
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input.",
                "errors": serializer.errors,
            }, status=400)
        # save will trigger create method in TweetSerializerForCreate
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet, context={'request': request}).data,
            status=201,
        ) # 展示用的另一个serializer