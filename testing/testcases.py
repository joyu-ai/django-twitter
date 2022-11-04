from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase as DjangoTestCase
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from tweets.models import Tweet

class TestCase(DjangoTestCase):

    @property
    def anonymous_client(self):
        # 因为anonymous_client 太常用了，就放到了 Testing -> testcase.py 里
        # QuerySet 也有 cache，instance level 的 cache
        # 避免同一个 instance 访问同一个数据两次时，产生重复计算
        # 总结到 OneNote
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = f'{username}@twitter.com'
        # 不能写成 User.objects.create()
        # 因为 password 需要被加密，username 和 email 需要进行一些 normalize 处理
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(user=user, tweet=tweet)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'default comment content'
        return Comment.objects.create(user=user, tweet=tweet, content=content)

    def create_like(self, user, target):
        # user 要点赞 target
        # target is comment or tweet
        # 怎么去取得 target 对应的类的名字呢
        # target.__class__ 但是类名他在数据库里是没有记录的
        # ContentType.objects.get_for_model() 会帮你找到 类名对应的 ContentType id
        # return Like.objects.create(
        #     content_type=ContentType.objects.get_for_model(target.__class__),
        #     object_id=target.id,
        #     user=user,
        # )

        # 直接创建好了，一般来说也不会多次创建 => 不行，必须用 get_or_create，为了 test
        # 第二个返回的是他是 get 出来的还是 create 出来的
        instance, _ = Like.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(target.__class__),
            object_id=target.id,
            user=user,
        )
        return instance

    def create_user_and_client(self, *args, **kwargs):
        user = self.create_user(*args, **kwargs)
        client = APIClient()
        client.force_authenticate(user)
        return user, client