# 这个admin就是Django自己的admin
from django.contrib import admin
from tweets.models import Tweet, TweetPhoto


@admin.register(Tweet) # decorator
class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at' # 可以按照时间进行筛选
    list_display = (
        'created_at',
        'user',
        'content',
    )


@admin.register(TweetPhoto)
class TweetPhotoAdmin(admin.ModelAdmin):
    list_display = (
        'tweet',
        'user',
        'file',
        'status',
        'has_deleted',
        'created_at',
    )
    list_filter = ('status', 'has_deleted')
    date_hierarchy = 'created_at'