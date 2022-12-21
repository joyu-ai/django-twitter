from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
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
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        page = self.paginator.paginate_cached_list(cached_newsfeeds, request)
        # page 是 None 代表我现在请求的数据可能不在 cache 里，需要直接去 db 来获取
        if page is None:
            queryset = NewsFeed.objects.filter(user=request.user)
            page = self.paginate_queryset(queryset)
        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
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