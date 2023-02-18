from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_client import RedisClient
from newsfeeds.tasks import fanout_newsfeeds_main_task
from gatekeeper.models import GateKeeper

class NewsFeedServiceTests(TestCase):

    def setUp(self):
        super(NewsFeedServiceTests, self).setUp()
        self.linghu = self.create_user('linghu')
        self.dongxie = self.create_user('dongxie')

    def test_get_user_newsfeeds(self):
        newsfeed_timestamps = []
        for i in range(3):
            tweet = self.create_tweet(self.dongxie)
            newsfeed = self.create_newsfeed(self.linghu, tweet)
            newsfeed_timestamps.append(newsfeed.created_at)
        newsfeed_timestamps = newsfeed_timestamps[::-1]

        # cache miss
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

        # cache hit
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

        # cache updated
        tweet = self.create_tweet(self.linghu)
        new_newsfeed = self.create_newsfeed(self.linghu, tweet)
        newsfeeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        newsfeed_timestamps.insert(0, new_newsfeed.created_at)
        self.assertEqual([f.created_at for f in newsfeeds], newsfeed_timestamps)

    def test_create_new_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(self.linghu, self.create_tweet(self.linghu))

        self.clear_cache()
        conn = RedisClient.get_connection()

        key = USER_NEWSFEEDS_PATTERN.format(user_id=self.linghu.id)
        self.assertEqual(conn.exists(key), False)
        feed2 = self.create_newsfeed(self.linghu, self.create_tweet(self.linghu))
        self.assertEqual(conn.exists(key), True)

        feeds = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(
            [f.created_at for f in feeds],
            [feed2.created_at, feed1.created_at]
        )

class NewsFeedTaskTests(TestCase):

    def setUp(self):
        super(NewsFeedTaskTests, self).setUp()
        self.linghu = self.create_user('linghu')
        self.dongxie = self.create_user('dongxie')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.linghu, 'tweet 1')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = tweet.timestamp
        else:
            created_at = tweet.created_at
        self.create_friendship(self.dongxie, self.linghu)
        msg = fanout_newsfeeds_main_task(tweet.id, created_at, self.linghu.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeedService.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.linghu)
        tweet = self.create_tweet(self.linghu, 'tweet 2')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = tweet.timestamp
        else:
            created_at = tweet.created_at
        msg = fanout_newsfeeds_main_task(tweet.id, created_at, self.linghu.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeedService.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.linghu)
        tweet = self.create_tweet(self.linghu, 'tweet 3')
        if GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
            created_at = tweet.timestamp
        else:
            created_at = tweet.created_at
        msg = fanout_newsfeeds_main_task(tweet.id, created_at, self.linghu.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeedService.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.dongxie.id)
        self.assertEqual(len(cached_list), 3)