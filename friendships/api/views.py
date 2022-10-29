from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from friendships.models import Friendship
from friendships.api.serializers import (
    FollowingSerializer,
    FollowerSerializer,
    FriendshipSerializerForCreate,
)
from django.contrib.auth.models import User


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FriendshipSerializerForCreate
    queryset = User.objects.all()

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        # GET /api/friendships/1/followers/
        # friendships = Friendship.objects.filter(to_user_id=pk).order_by('-created_at')

        # 可以在这里去掉 order_by，在model.py 里加上默认按时间逆序排列
        friendships = Friendship.objects.filter(to_user_id=pk)
        serializer = FollowerSerializer(friendships, many=True)
        return Response(
            {'followers': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        # GET /api/friendships/1/followings/
        # friendships = Friendship.objects.filter(from_user_id=pk).order_by('-created_at')

        # 可以在这里去掉 order_by，在model.py 里加上默认按时间逆序排列
        friendships = Friendship.objects.filter(from_user_id=pk)
        serializer = FollowingSerializer(friendships, many=True)
        return Response(
            {'followings': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # 再另一种写法，因为 L16 queryset：
        # check if user with id=pk exists
        # self.get_object() # 他会检测这个pk在不在，返回404

        # 另一种写法 400 返回
        # /api/friendships/<pk>/follow/

        serializer = FriendshipSerializerForCreate(data={
            'from_user_id': request.user.id,
            'to_user_id': pk,
        })

        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        #serializer.save()
        #return Response({'success': True}, status=status.HTTP_201_CREATED)
        # 显示更多内容：
        instance = serializer.save()
        return Response(
            FollowingSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk):
        # self.get_object()
        # 注意 pk 的类型是 str，所以要做类型转换
        # if request.user.id == int(pk): # 1 != '1'

        # 你可以把 unfollow_user 取出来
        # raise 404
        unfollow_user = self.get_object()
        if request.user.id == unfollow_user.id:
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself',
            }, status=status.HTTP_400_BAD_REQUEST)

        #
        # Queryset 的 delete 操作返回两个值，一个是删了多少数据，一个是具体美中类型删了多少
        # 为什么会出现多种类型数据的删除？因为可能因为 foreign key 设置了 cascade 出现级联
        # 删除，也就是比如 A model 的某个属性是 B model 的 foreign key，并且设置了
        # on_delete=models.CASCADE, 那么当 B 的某个数据被删除的时候，A 中的关联也会被删除。
        # 所以 CASCADE 是很危险的，我们一般最好不要用，而是用 on_delete=models.SET_NULL
        # 取而代之，这样至少可以避免误删除操作带来的多米诺效应。
        deleted, _ = Friendship.objects.filter(
            from_user=request.user,
            to_user=unfollow_user,
        ).delete()
        return Response({'success': True, 'deleted': deleted})

        # MySQL 工程应用（实时 web 开发）要避免：
        # 1. JOIN # O(n^2) 相当于表单乘表单
        # 2. CASCADE
        # 3. DROP FOREIGN KEY CONSTRAINT

    def list(self, request):
        return Response({'message': 'this is friendships home page'})