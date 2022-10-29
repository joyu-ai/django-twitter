from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetSerializerForCreate
from tweets.models import Tweet


class TweetViewSet(GenericViewSet):
    """
    API endpoint that allows users to create, list tweets
    """
    serializer_class = TweetSerializerForCreate

    def get_permissions(self):
        if self.action == 'list':  # self.action 指调用的带request的函数
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request): # 只有加了view function，才会在api root页面看到链接。
        """
        重载 list方法，不列出所有 tweets，必须要求指定 user_id 作为筛选条件。
        """
        if 'user_id' not in request.query_params:
            return Response('missing user_id', status=400)

        # 这句查询会被翻译为
        # select * from twitter_tweets
        # where user_id = xxx
        # order by create_at desc
        # 这句 SQL 查询会用到 user 和 created_at 的联合索引
        # 单纯的 user 索引是不够的
        user_id = request.query_params['user_id'] # user_id是一个字符串
        tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at') # 不需要转成int，支持str。
        serializer = TweetSerializer(tweets, many=True) # return list of dict
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
        return Response(TweetSerializer(tweet).data, status=201) # 展示用的另一个serializer