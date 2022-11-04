from likes.models import Like
from django.contrib.contenttypes.models import ContentType


class LikeService(object): # 这个没有放在 api 里，因为也可能被异步任务使用

    @classmethod
    def has_liked(cls, user, target):
        if user.is_anonymous:
            return False
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
            user=user,
        ).exists()