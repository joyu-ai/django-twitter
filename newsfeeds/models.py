from django.contrib.auth.models import User # we use django model for user api
from django.db import models
from django.db.models.signals import post_save
from newsfeeds.listeners import push_newsfeed_to_cache
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper


class NewsFeed(models.Model):
    # 注意这个 user 不是存储谁发了这条 tweet，而是谁可以看到这条 tweet
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 我们去 filter newsfeeds 时一定会带上 user
    # 如果我们不带 user 是没有办法 filter newsfeeds 的
    # 你看 newsfeeds，一定是某个用户的信息流
    class Meta:
        index_together = (('user', 'created_at'),)
        unique_together = (('user', 'tweet'),)
        # ordering = ('user', '-created_at')
        # 这里可以直接写成, 他的作用是拿去加在所有 queryset 的后面
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.created_at}  inbox of {self.user}: {self.tweet}'

    @ property
    def cached_tweet(self):
        return MemcachedHelper.get_object_through_cache(Tweet, self.tweet_id)


post_save.connect(push_newsfeed_to_cache, sender=NewsFeed)
