# 因为逻辑复杂，放在 views 或 serializers 里写太长
# 所以放在 services 里
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from notifications.signals import notify # 信息提醒机制, 不好，以后不要用
from tweets.models import Tweet


class NotificationService(object):

    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        if like.user == target.user:
            return
        if like.content_type == ContentType.objects.get_for_model(Tweet):
            notify.send(
                like.user,
                recipient=target.user,
                verb='liked your tweet',
                target=target,
            )
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                like.user,
                recipient=target.user,
                verb='liked your comment',
                target=target,
            )

    @classmethod
    def send_comment_notification(cls, comment):
        if comment.user == comment.tweet.user:
            return
        notify.send(
            comment.user,
            recipient=comment.tweet.user,
            verb='commented on your tweet',
            target=comment.tweet,
        )