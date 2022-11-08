from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'id',
            'actor_content_type', # User1
            'actor_object_id',    # User1
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'timestamp',
            'unread',
        )
#
# 不用加 recipient ，就是登录用户
# 用到了 3 个 generic foreign keys
# example 1：
#     User1 关注了你（recipient）
#     actor 就是 User1，verb 就是 followed。
#     action 和 target 就可以设为空。
# example 2：
#     User1 给你的帖子 tweet1 点了赞
#     actor = User1
#     target = tweet1
#     verb = 点赞
#     这样前端就可以去渲染了
# action 令狐没想到例子