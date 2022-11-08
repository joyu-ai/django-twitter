from django_filters.rest_framework import DjangoFilterBackend
from inbox.api.serializers import NotificationSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin, # 列出所有的 queryset 的 notification
):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ('unread',) # 是 ListModelMixin 用到了

    def get_queryset(self): # 覆盖了get_queryset, 因为用户只应该看到自己的notifications
        # return self.request.user.notifications.all()
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request, *args, **kwargs):
        # count = self.get_queryset().filter(unread=True).count()
        count = Notification.objects.filter(
            recipient=self.request.user,
            unread=True,
        ).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *args, **kwargs):
        updated_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({'marked_count': updated_count}, status=status.HTTP_200_OK)