from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        # 自定义 queryset, 因为 newsfeed 的查看是有权限的
        # 只能看 user=当前登录用户的 newsfeed
        # 也可以是 self.request.user.newsfeed_set.all()
        # 但是一般最好还是按照 NewsFeed.objects.filter 的方式写，更清晰直观
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        queryset = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(
            queryset,
            context={'request': request}, # 20.4 TweetSerial 扩展，被 NewsFeedSerializer 调用
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    # 12 - 26 行也可以合并成如下：
    # def list(self, request):
    #     queryset = NewsFeed.objects.filter(user=self.request.user)
    #     page = self.paginated_queryset(queryset)
    #     serializer = NewsFeedSerializer(
    #         page,
    #         context={'request': request},
    #         many=True,
    #     )
    #     return self.get_paginated_response(serializer.data)