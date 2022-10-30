from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


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