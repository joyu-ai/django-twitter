from utils.listeners import invalidate_object_cache


def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        # TODO HOMEWORK 给 Comment 使用类似的方法进行 likes_count 的统计
        return

    # 不可以使用 tweet.likes_count += 1; tweet.save() 的方式
    # 因此这个操作不是原子操作，必须使用 update 语句才是原子操作
    # 方法一
    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') + 1)
    # 方法二
    # tweet = instance.content_object
    # tweet.likes_count = F('likes_count') + 1
    # tweet.save()

def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        # TODO HOMEWORK 给 Comment 使用类似的方法进行 likes_count 的统计
        return

    # handle tweet likes cancel
    Tweet.objects.filter(id=instance.object_id).update(likes_count=F('likes_count') - 1)
