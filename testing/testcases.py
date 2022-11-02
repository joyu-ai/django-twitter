from comments.models import Comment
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
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

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'default comment content'
        return Comment.objects.create(user=user, tweet=tweet, content=content)