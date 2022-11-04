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
from utils.decorators import required_params

class TweetViewSet(GenericViewSet):
    """
    API endpoint that allows users to create, list tweets
    """
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()

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
        # 优化：下面两句用上面的 @required_params 取代
        # if 'user_id' not in request.query_params:
        #     return Response('missing user_id', status=400)
        # 为什么定义 request_attr
        # GET request.query_params
        # POST request.data

        # 这句查询会被翻译为
        # select * from twitter_tweets
        # where user_id = xxx
        # order by create_at desc
        # 这句 SQL 查询会用到 user 和 created_at 的联合索引
        # 单纯的 user 索引是不够的
        user_id = request.query_params['user_id'] # user_id是一个字符串
        tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at') # 不需要转成int，支持str。
        serializer = TweetSerializer(
            tweets,
            context={'request': request}, # 20.4 扩展了功能，令狐习惯传整个 request
            many=True,
        ) # return list of dict
        # 一般来说 json 格式的 response 默认都要用 hash 的格式
        # 而不能用 list 的格式（约定俗成）
        return Response({'tweets': serializer.data})

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