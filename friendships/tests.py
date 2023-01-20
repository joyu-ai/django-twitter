from django_hbase.models import EmptyColumnError, BadRowKeyError
from friendships.hbase_models import HBaseFollowing, HBaseFollower
from friendships.models import Friendship
from friendships.services import FriendshipService
from testing.testcases import TestCase

import time


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.linghu = self.create_user('linghu')
        self.dongxie = self.create_user('dongxie')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for to_user in [user1, user2, self.dongxie]:
            Friendship.objects.create(from_user=self.linghu, to_user=to_user)
        # FriendshipService.invalidate_following_cache(self.linghu.id) # 已用 listener

        user_id_set = FriendshipService.get_following_user_id_set(self.linghu.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id, self.dongxie.id})

        Friendship.objects.filter(from_user=self.linghu, to_user=self.dongxie).delete()
        # FriendshipService.invalidate_following_cache(self.linghu.id)
        user_id_set = FriendshipService.get_following_user_id_set(self.linghu.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id})


class HBaseTests(TestCase):

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        timestamp = self.ts_now
        following = HBaseFollowing(from_user_id=123, to_user_id=34, created_at=timestamp)
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.from_user_id, 123)
        self.assertEqual(instance.to_user_id, 34)
        self.assertEqual(instance.created_at, timestamp)

        following.to_user_id = 456
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.to_user_id, 456)

        # object does not exist, return None
        instance = HBaseFollowing.get(from_user_id=123, created_at=self.ts_now)
        self.assertEqual(instance, None)

    def test_create_and_get(self):
        # missing column data, can not store in hbase
        try:
            HBaseFollower.create(to_user_id=1, created_at=self.ts_now)
            exception_raised = False
        except EmptyColumnError:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # invalid row_key
        try:
            HBaseFollower.create(from_user_id=1, to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key')
        self.assertEqual(exception_raised, True)

        ts = self.ts_now
        HBaseFollower.create(from_user_id=1, to_user_id=2, created_at=ts)
        instance = HBaseFollower.get(to_user_id=2, created_at=ts)
        self.assertEqual(instance.from_user_id, 1)
        self.assertEqual(instance.to_user_id, 2)
        self.assertEqual(instance.created_at, ts)

        # can not get if row key missing
        try:
            HBaseFollower.get(to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in row key')
        self.assertEqual(exception_raised, True)

    def test_filter(self):
        HBaseFollowing.create(from_user_id=1, to_user_id=2, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=3, created_at=self.ts_now)
        HBaseFollowing.create(from_user_id=1, to_user_id=4, created_at=self.ts_now)


        followings = HBaseFollowing.filter(prefix=(1, None))
        self.assertEqual(3, len(followings))
        self.assertEqual(followings[0].from_user_id, 1)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].from_user_id, 1)
        self.assertEqual(followings[1].to_user_id, 3)
        self.assertEqual(followings[2].from_user_id, 1)
        self.assertEqual(followings[2].to_user_id, 4)


        # test limit
        results = HBaseFollowing.filter(prefix=(1, None), limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].to_user_id, 2)


        results = HBaseFollowing.filter(prefix=(1, None), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 2)
        self.assertEqual(results[1].to_user_id, 3)


        results = HBaseFollowing.filter(prefix=(1, None), limit=4)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].to_user_id, 2)
        self.assertEqual(results[1].to_user_id, 3)
        self.assertEqual(results[2].to_user_id, 4)


        results = HBaseFollowing.filter(start=(1, results[1].created_at), limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 3)
        self.assertEqual(results[1].to_user_id, 4)


        # test reverse
        results = HBaseFollowing.filter(prefix=(1, None), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 4)
        self.assertEqual(results[1].to_user_id, 3)


        results = HBaseFollowing.filter(start=(1, results[1].created_at), limit=2, reverse=True)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].to_user_id, 3)
        self.assertEqual(results[1].to_user_id, 2)