from django.contrib.auth.models import User
from django_hbase import models
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper


class HBaseNewsFeed(models.HBaseModel):
    # 注意这个 user 不是存储谁发了这条 tweet，而是谁可以看到这条 tweet
    user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    tweet_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_newsfeeds'
        row_key = ('user_id', 'created_at')

    def __str__(self):
        return '{} inbox of {}: {}'.format(self.created_at, self.user_id, self.tweet_id)

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_through_cache(Tweet, self.tweet_id)

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)