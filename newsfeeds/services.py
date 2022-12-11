from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService(object):

    # 错误的方法
    # 不可以将数据库操作放在 for 循环里面，效率会非常低
    # def fanout_to_followers(self, tweet):
    #     followers = FriendshipService.get_followers(tweet.user)
    #     # production 里是不允许 for + query
    #     # web <-> db 通常不是一台机器，就算在同一台机架上也是有延时的，总结到 OneNote
    #     for follower in followers:
    #         NewsFeed.objects.create(user=follower, tweet=tweet)

    # 正确的方法：使用 bulk_create，会把 insert 语句合成一条
    @classmethod
    def fanout_to_followers(cls, tweet):
        # new 一个 newsfeed 的 instance，只要我还没对他 .save()，他不会产生数据库的请求
        # 我先把要请求的 instance 给 new 好
        # 把 N 次的 insert into 变成了一次 insert into
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)

        # bulk create 不会触发 post_save 的 signal，所以需要手动 push 到 cache 里
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)