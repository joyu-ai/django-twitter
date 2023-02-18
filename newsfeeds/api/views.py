from django.utils.decorators import method_decorator
from gatekeeper.models import GateKeeper
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed, HBaseNewsFeed
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
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

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(request.user.id)
        page = self.paginator.paginate_cached_list(cached_newsfeeds, request)
        if page is None:
            if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
                page = self.paginator.paginate_hbase(
                    HBaseNewsFeed,
                    (request.user.id,),
                    request,
                )
            else:
                queryset = NewsFeed.objects.filter(user=request.user)
                page = self.paginate_queryset(queryset)

        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)