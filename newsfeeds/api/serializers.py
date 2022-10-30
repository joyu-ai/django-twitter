from rest_framework import serializers
from newsfeeds.models import NewsFeed
from tweets.api.serializers import TweetSerializer


class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer()

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'tweet')
        # 这三个是从 NewsFeed 里来？
        # tweet = TweetSerializer() overwrite 了 NewsFeed 里的 tweet？
        # 去掉第7行看看