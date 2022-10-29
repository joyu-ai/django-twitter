from django.db import models
from django.contrib.auth.models import User
from utils.time_helpers import utc_now


class Tweet(models.Model):
    # user 就是指这篇帖子是谁发的。
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text='who posted the tweet',
        # verbose_name=u'谁发了这个帖'
    )
    content = models.CharField(max_length=255) # CharField 就够了，因为是微博。之前用TextField。
    created_at = models.DateTimeField(auto_now_add=True)

    # 联合索引
    class Meta:
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')

    @property
    def hours_to_now(self):
        # datetime.now 不带时区信息，需要增加上 utc 的时区信息
        return (utc_now() - self.created_at).seconds // 3600

    def __str__(self):
        # 这里是你执行 print(tweet instance) 的时候会显示的内容。
        return f'{self.created_at} {self.user}: {self.content}'