from rest_framework import serializers
from newsfeeds.models import NewsFeed
from tweets.api.serializers import TweetSerializer


# 20.4 TweetSerializer 扩展，要传 context
# 这里不能传给 TweetSerializer
# 要查 NewsFeedSerializer 是被谁用到的，传入那里
class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer(source='cached_tweet')

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'tweet')
        # 这三个是从 NewsFeed 里来？
        # tweet = TweetSerializer() overwrite 了 NewsFeed 里的 tweet？
        # 去掉第7行看看