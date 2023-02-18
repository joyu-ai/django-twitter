from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.constants import FANOUT_BATCH_SIZE
from utils.time_constants import ONE_HOUR

@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, created_at, follower_ids):
    # import 写在里面避免循环依赖
    from newsfeeds.services import NewsFeedService
    batch_params = [
        {'user_id': follower_id, 'created_at': created_at, 'tweet_id': tweet_id}
        for follower_id in follower_ids
    ]
    newsfeeds = NewsFeedService.batch_create(batch_params)
    return "{} newsfeeds created".format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, created_at, tweet_user_id):
    # import 写在里面避免循环依赖
    from newsfeeds.services import NewsFeedService

    # 将推给自己的 Newsfeed 率先创建，确保自己能最快看到
    NewsFeedService.create(
        user_id=tweet_user_id,
        tweet_id=tweet_id,
        created_at=created_at,
    )

    # 获得所有的 follower ids，按照 batch size 拆分开
    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, created_at, batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )