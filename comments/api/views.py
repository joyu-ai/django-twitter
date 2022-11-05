from comments.api.permissions import IsObjectOwner
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate
)
from comments.models import Comment
from inbox.services import NotificationService
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utils.decorators import required_params


# 尽量不要继承ModelViewSet。他默认增删查改都可以做
# 但实际上不是这样的。很多时候有很多权限问题
# 以白名单的方式，就是需要什么加什么，最好
class CommentViewSet(viewsets.GenericViewSet):
    """
    只实现 list, create, update, destroy 的方法
    不实现 retrieve（查询单个 comment） 的方法，因为没这个需求
    """
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)
    # 我可以拿着 queryset 去 filter tweet_id
    # 写成 tuple() 不可更改比较好。不用 list[]。

    def get_permissions(self):
        # 注意要加用 AllowAny() / IsAuthenticated() 实例化出对象
        # 而不是 AllowAny / IsAuthenticated 这样只是一个类名
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()] # 按顺序，一旦前面出错，后面就不检测了
        return [AllowAny()]

    @required_params(params=['tweet_id'])
    def list(self, request, *args, **kwargs):
        # 优化：用decorator
        # if 'tweet_id' not in request.query_params:
        #     # return Response(
        #     #     {
        #     #         'message': 'missing tweet_id in request',
        #     #         'success': False,
        #     #     },
        #     #     status=status.HTTP_400_BAD_REQUEST,
        #     # )
        #     # 另外一个风格也可以，省一个缩进，省两行
        #     # 只有一个status时比较适合
        #     return Response({
        #         'message': 'missing tweet_id in request',
        #         'success': False,
        #     },status=status.HTTP_400_BAD_REQUEST,)

        # # 可以如下写，也比较简洁
        # # 坏处是, 当筛选的条件变多时，就不简洁了
        # tweet_id = request.query_params['tweet_id']
        # comments = Comment.objects.filter(tweet_id=tweet_id)
        # serializer = CommentSerializer(comments, many=True)
        # return Response(
        #     {'comment': serializer.data},
        #     status=status.HTTP_200_OK,
        # )

        # 所以用了以个 django_filters 的包
        # 去拿到 filter 完之后的 queryset
        # 好处是，如果有 多个筛选条件，可以直接在前面的 filterset_fields 里加
        queryset = self.get_queryset() # 这个就是Comment.objects.all()
        # comments = self.filter_queryset(queryset).order_by('created_at') #这个就是 filter 后的
        comments = self.filter_queryset(queryset)\
            .prefetch_related('user')\
            .order_by('created_at')
        serializer = CommentSerializer(
            comments,
            context={'request': request},
            many=True
        )
        return Response(
            {'comments': serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }
        # 注意这里必须要加 'data=' 来指定参数是传给 data 的
        # 因为默认的第一个参数是 instance
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save 方法会触发 serializer 里的 create 方法，点进 save 的具体实现里可以看到
        comment = serializer.save()
        NotificationService.send_comment_notification(comment)
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        # get_object 是 DRF 包装的一个函数，会在找不到的时候 raise 404 error
        # 所以这里无需做额外判断
        # 等同于 Comments.objects.all().get(id=url解析出来的id）
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            instance=comment,
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        # save 方法会触发 serializer 里的 update 方法，点进 save 的具体实现里可以看到
        # save 是根据 instance 参数有没有传来决定是触发 create 还是 update
        comment = serializer.save()
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        # DRF 里默认 destroy 返回的是 status code = 204 no content
        # 这里 return 了 success=True 更直观的让前端去做判断，所以 return 200 更合适
        return Response({'success': True}, status=status.HTTP_200_OK)